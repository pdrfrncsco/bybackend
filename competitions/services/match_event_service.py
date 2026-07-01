"""
BOLAYETU — MatchEventService (Phase 4: Match Center)

Business logic for recording and managing in-game match events.
Goals automatically recalculate the home/away score on the Match row.
"""

from django.db import transaction
from core.models import Tenant
from clubs.models import Club
from players.models import Player
from competitions.models import Match, MatchEvent


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
    ) -> MatchEvent:
        """
        Record a new in-game event. If it's a goal type, recalculates score.

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

        if not (0 <= minute <= 120):
            raise InvalidMatchEventData("minute must be between 0 and 120.")

        # Validate club is in this match
        if club.id not in (match.home_club_id, match.away_club_id):
            raise InvalidMatchEventData("Club is not participating in this match.")

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
        )

        # Auto-recalculate score from goal events
        goal_types = {
            MatchEvent.EventType.GOAL,
            MatchEvent.EventType.PENALTY_SCORED,
            MatchEvent.EventType.OWN_GOAL,
        }
        if event_type in goal_types:
            MatchEventService._recalculate_score(match)

        return event

    @staticmethod
    @transaction.atomic
    def remove_event(*, tenant: Tenant, event_id: str) -> None:
        """
        Delete an event. Recalculates score if it was a goal.
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
        from competitions.models import Match

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
