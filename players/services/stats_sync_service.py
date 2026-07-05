"""
BOLAYETU — Player Stats Sync Service

Automatically synchronizes player statistics from MatchEvents to PlayerRegistration.

Architecture:
    - Called by MatchEventService after event creation/deletion
    - Updates PlayerRegistration stats (per club/season)
    - Propagates totals to global Player entity
    - Uses atomic transactions to ensure consistency
"""

import logging
from typing import Optional

from django.db import transaction
from django.db.models import Q, Count

from players.models import Player, PlayerRegistration
from competitions.models import Match, MatchEvent
from clubs.models import Club

logger = logging.getLogger("players")


class StatsSyncService:
    """
    Synchronizes player statistics from match events to registration records.
    
    Stats are aggregated per player+club+competition combination and stored
    in PlayerRegistration. Totals are then propagated to the global Player.
    """

    @staticmethod
    @transaction.atomic
    def sync_player_stats_from_event(
        event: MatchEvent,
        operation: str = "add",
    ) -> Optional[PlayerRegistration]:
        """
        Sync stats for a player after a MatchEvent is added or removed.
        
        Args:
            event: The MatchEvent that was added or will be removed
            operation: "add" for new event, "remove" for deleted event
            
        Returns:
            The updated PlayerRegistration or None if player not found
        """
        if not event.player:
            logger.debug("Event has no player, skipping stats sync")
            return None
        
        player = event.player
        club = event.club
        match = event.match
        
        # Find the active registration for this player+club+competition
        registration = PlayerRegistration.objects.filter(
            player=player,
            club=club,
            competition=match.competition,
            status__in=[
                PlayerRegistration.RegistrationStatus.REGISTERED,
                PlayerRegistration.RegistrationStatus.LOANED,
            ],
        ).first()
        
        if not registration:
            # Try to find any registration for this player+club (without competition)
            registration = PlayerRegistration.objects.filter(
                player=player,
                club=club,
                status__in=[
                    PlayerRegistration.RegistrationStatus.REGISTERED,
                    PlayerRegistration.RegistrationStatus.LOANED,
                ],
            ).exclude(competition__isnull=False).first()
        
        if not registration:
            logger.warning(
                "No active registration found for player %s at club %s",
                player.full_name, club.name
            )
            return None
        
        # Recalculate stats from all events for this registration
        StatsSyncService._recalculate_registration_stats(registration)
        
        # Propagate totals to global Player
        StatsSyncService._update_player_totals(player)
        
        logger.info(
            "Synced stats for %s (event: %s, operation: %s)",
            player.full_name, event.event_type, operation
        )
        
        return registration

    @staticmethod
    def _recalculate_registration_stats(registration: PlayerRegistration) -> None:
        """
        Recalculate all stats for a PlayerRegistration from MatchEvents.
        
        Stats are derived from events in matches where:
            - The match competition matches the registration competition (if set)
            - The player's club is participating
        """
        player = registration.player
        club = registration.club
        competition = registration.competition
        
        # Build queryset for relevant matches
        matches_qs = Match.objects.filter(
            competition=competition,
        ).filter(
            Q(home_club=club) | Q(away_club=club)
        )
        
        match_ids = list(matches_qs.values_list("id", flat=True))
        
        # Count goals (including penalties)
        goals = MatchEvent.objects.filter(
            player=player,
            club=club,
            match_id__in=match_ids,
            event_type__in=[
                MatchEvent.EventType.GOAL,
                MatchEvent.EventType.PENALTY_SCORED,
            ],
        ).count()
        
        # Count own goals (tracked separately but not in basic stats)
        # own_goals = MatchEvent.objects.filter(
        #     player=player,
        #     club=club,
        #     match_id__in=match_ids,
        #     event_type=MatchEvent.EventType.OWN_GOAL,
        # ).count()
        
        # Count yellow cards
        yellow_cards = MatchEvent.objects.filter(
            player=player,
            club=club,
            match_id__in=match_ids,
            event_type=MatchEvent.EventType.YELLOW_CARD,
        ).count()
        
        # Count red cards (direct + second yellow)
        red_cards = MatchEvent.objects.filter(
            player=player,
            club=club,
            match_id__in=match_ids,
            event_type__in=[
                MatchEvent.EventType.RED_CARD,
                MatchEvent.EventType.YELLOW_RED,
            ],
        ).count()
        
        # Count assists (not directly tracked in events yet, keep existing)
        # For now, assists remain as manually set values
        # assists = registration.assists
        
        # Count matches played (distinct matches where player has events)
        matches_with_events = MatchEvent.objects.filter(
            player=player,
            club=club,
            match_id__in=match_ids,
        ).values_list("match_id", flat=True).distinct()
        
        matches_played = len(matches_with_events)
        
        # Update registration
        registration.goals = goals
        registration.yellow_cards = yellow_cards
        registration.red_cards = red_cards
        registration.matches_played = matches_played
        registration.save(update_fields=[
            "goals", "yellow_cards", "red_cards", "matches_played"
        ])
        
        logger.debug(
            "Updated registration stats for %s at %s: %d matches, %d goals, %d YC, %d RC",
            player.full_name, club.name, matches_played, goals, yellow_cards, red_cards
        )

    @staticmethod
    def _update_player_totals(player: Player) -> None:
        """
        Update denormalized totals on the global Player entity.
        
        Aggregates all registrations to compute:
            - total_matches
            - total_goals
            - total_assists
        """
        from django.db.models import Sum
        
        totals = PlayerRegistration.objects.filter(player=player).aggregate(
            total_matches=Sum("matches_played"),
            total_goals=Sum("goals"),
            total_assists=Sum("assists"),
        )
        
        player.total_matches = totals["total_matches"] or 0
        player.total_goals = totals["total_goals"] or 0
        player.total_assists = totals["total_assists"] or 0
        player.save(update_fields=["total_matches", "total_goals", "total_assists"])
        
        logger.debug(
            "Updated player totals for %s: %d matches, %d goals, %d assists",
            player.full_name, player.total_matches, player.total_goals, player.total_assists
        )

    @staticmethod
    @transaction.atomic
    def sync_all_player_stats(player: Player) -> None:
        """
        Force recalculation of all stats for a player.
        
        Useful for data migrations or manual corrections.
        """
        registrations = PlayerRegistration.objects.filter(player=player)
        
        for registration in registrations:
            StatsSyncService._recalculate_registration_stats(registration)
        
        StatsSyncService._update_player_totals(player)
        
        logger.info("Force-synced all stats for player %s", player.full_name)
