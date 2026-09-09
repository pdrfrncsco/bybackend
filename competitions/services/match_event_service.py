"""
BOLAYETU — MatchEventService (Phase 4: Match Center)

Business logic for recording and managing in-game match events.
Goals automatically recalculate the home/away score on the Match row.
Player stats are automatically synced to PlayerRegistration.
"""

from django.db import transaction
from core.models import Tenant
from clubs.models import Club
from players.models import Player
from competitions.models import Match, MatchEvent
from core.events import Event, EventType, publish_event


class MatchEventNotFound(Exception):
    pass


class InvalidMatchEventData(Exception):
    pass


class MatchEventService:
    """Handles recording, updating and deleting in-game events."""

    # ── Core helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _recalculate_score(match: Match) -> None:
        """
        Recomputes home_score / away_score from goal events and saves the match.
        Called after any create/delete of a goal event.
        """
        events = MatchEvent.objects.filter(match=match)
        home_score = 0
        away_score = 0
        for ev in events:
            if ev.event_type in (MatchEvent.EventType.GOAL, MatchEvent.EventType.PENALTY_SCORED):
                # Goal for the club attributed — need to determine home/away
                if ev.club_id == match.home_club_id:
                    home_score += 1
                else:
                    away_score += 1
            elif ev.event_type == MatchEvent.EventType.OWN_GOAL:
                # Own goal: scored against own club
                if ev.club_id == match.home_club_id:
                    away_score += 1  # home team scored an own goal → away gets point
                else:
                    home_score += 1
        match.home_score = home_score
        match.away_score = away_score
        match.save(update_fields=["home_score", "away_score", "updated_at"])

    @staticmethod
    def _sync_player_stats(event: MatchEvent, operation: str = "add") -> None:
        """
        Sync player stats to PlayerRegistration after event add/remove.
        
        Uses StatsSyncService to update:
            - PlayerRegistration stats (per club/competition)
            - Global Player totals (denormalized)
        """
        from players.services.stats_sync_service import StatsSyncService
        
        StatsSyncService.sync_player_stats_from_event(event, operation)

    # ── Public API ────────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def add_event(
        *,
        tenant: Tenant,
        match: Match,
        club: Club,
        event_type: str,
        minute: int,
        player: Player | None = None,
        player_off: Player | None = None,
        extra_time: bool = False,
        notes: str = "",
        idempotency_key: str | None = None,
    ) -> MatchEvent:
        """
        Record a new in-game event. If it's a goal type, recalculates score.
        Automatically syncs player stats to PlayerRegistration.

        Args:
            tenant: The organisation/tenant context.
            match: The match the event belongs to.
            club: Club attributed to the event.
            event_type: One of MatchEvent.EventType choices.
            minute: Match minute (0-120).
            player: Primary player (scorer, fouled player, player going off/on).
            player_off: For SUBSTITUTION_IN: the player being replaced.
            extra_time: Whether this is a stoppage-time minute.
            notes: Free-text notes.

        Returns:
            The created MatchEvent instance.
        """
        if event_type not in MatchEvent.EventType.values:
            raise InvalidMatchEventData(f"Unknown event_type: {event_type!r}")

        if not (0 <= minute <= 135):
            raise InvalidMatchEventData("minute must be between 0 and 135.")

        # Validate club is in this match
        if club.id not in (match.home_club_id, match.away_club_id):
            raise InvalidMatchEventData("Club is not participating in this match.")

        if idempotency_key:
            existing = MatchEvent.objects.filter(
                tenant=tenant, match=match, idempotency_key=idempotency_key,
            ).first()
            if existing:
                return existing

        event = MatchEvent.objects.create(
            tenant=tenant,
            match=match,
            club=club,
            event_type=event_type,
            minute=minute,
            player=player,
            player_off=player_off,
            extra_time=extra_time,
            notes=notes,
            idempotency_key=idempotency_key or None,
        )

        # Auto-recalculate score from goal events
        goal_types = {
            MatchEvent.EventType.GOAL,
            MatchEvent.EventType.PENALTY_SCORED,
            MatchEvent.EventType.OWN_GOAL,
        }
        if event_type in goal_types:
            MatchEventService._recalculate_score(match)

        # Update substitution minutes on MatchLineup if applicable
        if event_type == MatchEvent.EventType.SUBSTITUTION_IN:
            from competitions.models import MatchLineup
            if player:
                MatchLineup.objects.filter(
                    tenant=tenant, match=match, club=club, player=player
                ).update(substituted_in_minute=minute)
            if player_off:
                MatchLineup.objects.filter(
                    tenant=tenant, match=match, club=club, player=player_off
                ).update(substituted_out_minute=minute)

        # Auto-check Fair Play suspensions for cards
        card_types = {
            MatchEvent.EventType.YELLOW_CARD,
            MatchEvent.EventType.RED_CARD,
            MatchEvent.EventType.YELLOW_RED,
        }
        if event_type in card_types:
            try:
                from competitions.services.fair_play_service import FairPlayService, SuspensionAlreadyExists
                FairPlayService.check_and_create_suspension_for_event(
                    tenant=tenant, event=event
                )
            except Exception:
                # Log or tolerate if already exists / handled
                pass

        # Auto-sync player stats
        MatchEventService._sync_player_stats(event, operation="add")
        publish_event(Event(
            type=EventType.MATCH_EVENT_CREATED,
            tenant_id=str(tenant.id),
            payload={
                "match_id": str(match.id),
                "event_id": str(event.id),
                "event_type": event.event_type,
                "minute": event.minute,
            },
            origin="competitions.match_event_service",
        ))

        return event

    @staticmethod
    @transaction.atomic
    def remove_event(*, tenant: Tenant, event_id: str) -> None:
        """
        Delete an event. Recalculates score if it was a goal.
        Automatically syncs player stats after removal.
        """
        try:
            event = MatchEvent.objects.select_related("match").get(
                id=event_id, tenant=tenant
            )
        except MatchEvent.DoesNotExist:
            raise MatchEventNotFound(f"MatchEvent {event_id} not found.")

        match = event.match
        was_goal = event.event_type in {
            MatchEvent.EventType.GOAL,
            MatchEvent.EventType.PENALTY_SCORED,
            MatchEvent.EventType.OWN_GOAL,
        }
        
        # Clean up any automatic suspension triggered by this event
        if event.event_type in {
            MatchEvent.EventType.YELLOW_CARD,
            MatchEvent.EventType.RED_CARD,
            MatchEvent.EventType.YELLOW_RED,
        }:
            from competitions.models import PlayerSuspension
            PlayerSuspension.objects.filter(
                tenant=tenant,
                trigger_event=event,
                status__in=[
                    PlayerSuspension.SuspensionStatus.PENDING,
                    PlayerSuspension.SuspensionStatus.ACTIVE,
                ],
            ).delete()

        # Clean up substitution minutes if it was a substitution
        if event.event_type == MatchEvent.EventType.SUBSTITUTION_IN:
            from competitions.models import MatchLineup
            if event.player:
                MatchLineup.objects.filter(
                    tenant=tenant, match=match, club=event.club, player=event.player
                ).update(substituted_in_minute=None)
            if event.player_off:
                MatchLineup.objects.filter(
                    tenant=tenant, match=match, club=event.club, player=event.player_off
                ).update(substituted_out_minute=None)

        # Sync player stats BEFORE deletion (need event data)
        MatchEventService._sync_player_stats(event, operation="remove")

        publish_event(Event(
            type=EventType.MATCH_EVENT_REMOVED,
            tenant_id=str(tenant.id),
            payload={"match_id": str(match.id), "event_id": str(event.id)},
            origin="competitions.match_event_service",
        ))

        event.delete()

        if was_goal:
            MatchEventService._recalculate_score(match)

    @staticmethod
    def list_events_for_match(*, tenant: Tenant, match_id: str) -> list[MatchEvent]:
        """Return all events for a match ordered by minute."""
        return list(
            MatchEvent.objects.filter(match_id=match_id, tenant=tenant)
            .select_related("player", "player_off", "club")
            .order_by("minute", "created_at")
        )

    @staticmethod
    def get_player_stats_for_competition(
        *, tenant: Tenant, competition_id: str
    ) -> list[dict]:
        """
        Aggregate per-player stats for a competition:
        goals, own_goals, yellow_cards, red_cards, appearances (distinct matches).
        Returns a list of dicts sorted by goals desc.
        """
        from django.db.models import Count, Q

        players_qs = (
            MatchEvent.objects.filter(
                tenant=tenant,
                match__competition_id=competition_id,
            )
            .values(
                "player_id",
                "player__first_name",
                "player__last_name",
                "player__avatar",
                "club_id",
                "club__name",
            )
            .annotate(
                goals=Count(
                    "id",
                    filter=Q(event_type__in=[
                        MatchEvent.EventType.GOAL,
                        MatchEvent.EventType.PENALTY_SCORED,
                    ]),
                ),
                own_goals=Count(
                    "id",
                    filter=Q(event_type=MatchEvent.EventType.OWN_GOAL),
                ),
                yellow_cards=Count(
                    "id",
                    filter=Q(event_type=MatchEvent.EventType.YELLOW_CARD),
                ),
                red_cards=Count(
                    "id",
                    filter=Q(event_type__in=[
                        MatchEvent.EventType.RED_CARD,
                        MatchEvent.EventType.YELLOW_RED,
                    ]),
                ),
                appearances=Count("match_id", distinct=True),
            )
            .order_by("-goals", "-appearances")
        )
        return list(players_qs)
