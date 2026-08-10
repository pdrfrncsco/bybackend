"""
BOLAYETU — Player Stats Sync Service

Automatically synchronizes player statistics from MatchEvents to PlayerRegistration,
and cascades updates to PlayerSeasonStatistics and PlayerFootballProfile.

Architecture:
    - Called by MatchEventService after event creation/deletion
    - Updates PlayerRegistration stats (per club/season)
    - Rebuilds PlayerSeasonStatistics (per club/season)
    - Propagates totals to global Player entity and FootballProfile
    - Uses atomic transactions to ensure consistency
"""

import logging
from typing import Optional

from django.db import transaction
from django.db.models import Q, Count, Sum

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
        
        # Rebuild PlayerSeasonStatistics from registrations
        StatsSyncService._rebuild_season_statistics(player, registration)
        
        # Propagate totals to global Player and FootballProfile
        StatsSyncService._update_player_totals(player)
        
        logger.info(
            "Synced stats for %s (event: %s, operation: %s)",
            player.full_name, event.event_type, operation
        )
        
        return registration

    @staticmethod
    def _recalculate_registration_stats(registration: PlayerRegistration) -> None:
        """
        Recalculate all stats for a PlayerRegistration from MatchEvents and MatchLineup.
        
        Stats are derived from:
            - MatchEvents: goals, cards, own goals
            - MatchLineup: minutes_played, starts
            - Matches where:
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
        
        # Aggregate minutes_played and starts from MatchLineup
        from competitions.models import MatchLineup
        lineups = MatchLineup.objects.filter(
            player=player,
            club=club,
            match_id__in=match_ids,
        )
        
        total_minutes = 0
        starts = 0
        for lineup in lineups:
            if lineup.minutes_played:
                total_minutes += lineup.minutes_played
            if lineup.status == MatchLineup.LineupStatus.STARTER:
                starts += 1
        
        # Update registration
        registration.goals = goals
        registration.yellow_cards = yellow_cards
        registration.red_cards = red_cards
        registration.matches_played = matches_played
        registration.save(update_fields=[
            "goals", "yellow_cards", "red_cards", "matches_played"
        ])
        
        logger.debug(
            "Updated registration stats for %s at %s: %d matches, %d goals, %d YC, %d RC, %d min, %d starts",
            player.full_name, club.name, matches_played, goals, yellow_cards, red_cards, total_minutes, starts
        )

    @staticmethod
    def _update_player_totals(player: Player) -> None:
        """
        Update denormalized totals on the global Player entity and FootballProfile.
        
        Aggregates all registrations to compute:
            - total_matches
            - total_goals
            - total_assists
        
        Also propagates to PlayerFootballProfile if it exists.
        """
        totals = PlayerRegistration.objects.filter(player=player).aggregate(
            total_matches=Sum("matches_played"),
            total_goals=Sum("goals"),
            total_assists=Sum("assists"),
        )
        
        player.total_matches = totals["total_matches"] or 0
        player.total_goals = totals["total_goals"] or 0
        player.total_assists = totals["total_assists"] or 0
        player.save(update_fields=["total_matches", "total_goals", "total_assists"])
        
        # Also update FootballProfile if it exists
        try:
            from players.models import PlayerFootballProfile
            profile = PlayerFootballProfile.objects.filter(player=player).first()
            if profile:
                profile.total_matches = player.total_matches
                profile.total_goals = player.total_goals
                profile.total_assists = player.total_assists
                profile.save(update_fields=["total_matches", "total_goals", "total_assists"])
                logger.debug("Updated FootballProfile totals for %s", player.full_name)
        except Exception as e:
            logger.warning("Could not update FootballProfile for %s: %s", player.full_name, e)
        
        logger.debug(
            "Updated player totals for %s: %d matches, %d goals, %d assists",
            player.full_name, player.total_matches, player.total_goals, player.total_assists
        )

    @staticmethod
    def _rebuild_season_statistics(player: Player, registration: PlayerRegistration = None) -> None:
        """
        Rebuild PlayerSeasonStatistics for a player after registration stats change.
        
        If a specific registration is provided, only that season/club combo is updated.
        Otherwise, the entire player's stats are rebuilt.
        """
        try:
            from players.services.player_statistics_service import PlayerStatisticsService
            PlayerStatisticsService.rebuild_for_player(player)
            logger.debug("Rebuilt season statistics for player %s", player.full_name)
        except Exception as e:
            logger.warning("Could not rebuild season statistics for %s: %s", player.full_name, e)

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
        
        StatsSyncService._rebuild_season_statistics(player)
        StatsSyncService._update_player_totals(player)
        
        logger.info("Force-synced all stats for player %s", player.full_name)
