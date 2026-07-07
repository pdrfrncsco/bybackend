"""
BOLAYETU — FairPlayService

Business logic for Fair Play management and automatic suspensions.

Key features:
    - Track yellow/red card accumulation per competition
    - Apply automatic suspensions based on configurable thresholds
    - Check player eligibility for matches
    - Generate fair play rankings

Default rules (configurable per competition):
    - 5 yellow cards → 1 match suspension
    - 10 yellow cards → 2 match suspension
    - 2 yellow cards in same match (yellow-red) → 1 match suspension
    - Direct red card → 1 match suspension (minimum)
"""

from django.db import models, transaction
from django.utils import timezone
from datetime import date
from typing import Optional

from core.models import Tenant
from players.models import Player
from clubs.models import Club
from competitions.models import Match, MatchEvent, Competition, PlayerSuspension


class FairPlayConfig:
    """Configuration for fair play rules."""
    
    # Yellow card thresholds
    YELLOW_THRESHOLD_1 = 5  # After 5 yellows, 1 match suspension
    YELLOW_THRESHOLD_2 = 10  # After 10 yellows, 2 match suspension
    YELLOW_THRESHOLD_3 = 15  # After 15 yellows, 3 match suspension
    
    # Suspension lengths
    YELLOW_SUSPENSION_1 = 1
    YELLOW_SUSPENSION_2 = 2
    YELLOW_SUSPENSION_3 = 3
    RED_CARD_SUSPENSION = 1
    YELLOW_RED_SUSPENSION = 1


class PlayerNotSuspended(Exception):
    pass


class SuspensionAlreadyExists(Exception):
    pass


class FairPlayService:
    """
    Handles Fair Play logic: card tracking, automatic suspensions,
    and eligibility checks.
    """

    # ─── Card Statistics ───────────────────────────────────────────────────────

    @staticmethod
    def get_player_cards_for_competition(
        *, 
        tenant: Tenant, 
        player: Player, 
        competition: Competition
    ) -> dict:
        """
        Get card statistics for a player in a competition.
        
        Returns:
            dict with yellow_cards, red_cards, yellow_reds counts
        """
        from django.db.models import Q
        
        events = MatchEvent.objects.filter(
            tenant=tenant,
            player=player,
            match__competition=competition,
        )
        
        yellow_cards = events.filter(
            event_type=MatchEvent.EventType.YELLOW_CARD
        ).count()
        
        red_cards = events.filter(
            event_type=MatchEvent.EventType.RED_CARD
        ).count()
        
        yellow_reds = events.filter(
            event_type=MatchEvent.EventType.YELLOW_RED
        ).count()
        
        return {
            "yellow_cards": yellow_cards,
            "red_cards": red_cards,
            "yellow_reds": yellow_reds,
            "total_cards": yellow_cards + red_cards + yellow_reds,
        }

    @staticmethod
    def get_player_cards_for_season(
        *,
        tenant: Tenant,
        player: Player,
        season: str
    ) -> dict:
        """Get card statistics for a player across all competitions in a season."""
        from django.db.models import Q
        
        events = MatchEvent.objects.filter(
            tenant=tenant,
            player=player,
            match__competition__season=season,
        )
        
        yellow_cards = events.filter(
            event_type=MatchEvent.EventType.YELLOW_CARD
        ).count()
        
        red_cards = events.filter(
            event_type=MatchEvent.EventType.RED_CARD
        ).count()
        
        yellow_reds = events.filter(
            event_type=MatchEvent.EventType.YELLOW_RED
        ).count()
        
        return {
            "yellow_cards": yellow_cards,
            "red_cards": red_cards,
            "yellow_reds": yellow_reds,
            "total_cards": yellow_cards + red_cards + yellow_reds,
        }

    # ─── Suspension Management ─────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def check_and_create_suspension_for_event(
        *,
        tenant: Tenant,
        event: MatchEvent
    ) -> Optional[PlayerSuspension]:
        """
        Check if an event should trigger an automatic suspension.
        Creates suspension if thresholds are met.
        
        Called automatically after adding a card event.
        
        Returns:
            PlayerSuspension if created, None otherwise
        """
        if not event.player:
            return None
        
        # Direct red card → automatic suspension
        if event.event_type == MatchEvent.EventType.RED_CARD:
            return FairPlayService.create_suspension(
                tenant=tenant,
                player=event.player,
                club=event.club,
                competition=event.match.competition,
                suspension_type=PlayerSuspension.SuspensionType.RED_CARD,
                matches_suspended=FairPlayConfig.RED_CARD_SUSPENSION,
                trigger_match=event.match,
                trigger_event=event,
                effective_from=date.today(),
                reason=f"Cartão vermelho direto no jogo {event.match}",
            )
        
        # Yellow-red (second yellow) → automatic suspension
        if event.event_type == MatchEvent.EventType.YELLOW_RED:
            return FairPlayService.create_suspension(
                tenant=tenant,
                player=event.player,
                club=event.club,
                competition=event.match.competition,
                suspension_type=PlayerSuspension.SuspensionType.YELLOW_RED,
                matches_suspended=FairPlayConfig.YELLOW_RED_SUSPENSION,
                trigger_match=event.match,
                trigger_event=event,
                effective_from=date.today(),
                reason=f"Segundo amarelo/cartão vermelho no jogo {event.match}",
            )
        
        # Yellow card → check accumulation threshold
        if event.event_type == MatchEvent.EventType.YELLOW_CARD:
            return FairPlayService._check_yellow_accumulation(
                tenant=tenant,
                player=event.player,
                club=event.club,
                competition=event.match.competition,
                current_event=event,
            )
        
        return None

    @staticmethod
    def _check_yellow_accumulation(
        *,
        tenant: Tenant,
        player: Player,
        club: Club,
        competition: Competition,
        current_event: MatchEvent
    ) -> Optional[PlayerSuspension]:
        """
        Check if yellow card accumulation reaches a threshold.
        Creates suspension if threshold is met.
        """
        # Get current yellow card count (including the new one)
        cards = FairPlayService.get_player_cards_for_competition(
            tenant=tenant,
            player=player,
            competition=competition,
        )
        yellow_count = cards["yellow_cards"]
        
        # Check thresholds (only trigger at exact threshold)
        matches_suspended = None
        threshold_reached = False
        
        if yellow_count == FairPlayConfig.YELLOW_THRESHOLD_3:
            matches_suspended = FairPlayConfig.YELLOW_SUSPENSION_3
            threshold_reached = True
        elif yellow_count == FairPlayConfig.YELLOW_THRESHOLD_2:
            matches_suspended = FairPlayConfig.YELLOW_SUSPENSION_2
            threshold_reached = True
        elif yellow_count == FairPlayConfig.YELLOW_THRESHOLD_1:
            matches_suspended = FairPlayConfig.YELLOW_SUSPENSION_1
            threshold_reached = True
        
        if threshold_reached and matches_suspended:
            return FairPlayService.create_suspension(
                tenant=tenant,
                player=player,
                club=club,
                competition=competition,
                suspension_type=PlayerSuspension.SuspensionType.YELLOW_ACCUMULATION,
                matches_suspended=matches_suspended,
                trigger_match=current_event.match,
                trigger_event=current_event,
                effective_from=date.today(),
                reason=f"Acumulação de {yellow_count} cartões amarelos na competição",
            )
        
        return None

    @staticmethod
    @transaction.atomic
    def create_suspension(
        *,
        tenant: Tenant,
        player: Player,
        club: Club,
        competition: Competition,
        suspension_type: str,
        matches_suspended: int,
        effective_from: date,
        trigger_match: Optional[Match] = None,
        trigger_event: Optional[MatchEvent] = None,
        reason: str = "",
        created_by=None,
    ) -> PlayerSuspension:
        """
        Create a new player suspension.
        
        Args:
            tenant: Organization
            player: Player being suspended
            club: Club the player is registered with
            competition: Competition where suspension applies
            suspension_type: Type of suspension
            matches_suspended: Number of matches to miss
            effective_from: Date suspension starts
            trigger_match: Match that triggered suspension (if any)
            trigger_event: Event that triggered suspension (if any)
            reason: Reason for suspension
            created_by: User who created the suspension (if manual)
        
        Returns:
            The created PlayerSuspension
        """
        # Check for duplicate active/pending suspension for same player/competition
        existing = PlayerSuspension.objects.filter(
            tenant=tenant,
            player=player,
            competition=competition,
            status__in=[
                PlayerSuspension.SuspensionStatus.PENDING,
                PlayerSuspension.SuspensionStatus.ACTIVE,
            ],
        ).exists()
        
        if existing:
            raise SuspensionAlreadyExists(
                f"Player {player.full_name} already has an active suspension in {competition.name}"
            )
        
        suspension = PlayerSuspension.objects.create(
            tenant=tenant,
            player=player,
            club=club,
            competition=competition,
            suspension_type=suspension_type,
            matches_suspended=matches_suspended,
            effective_from=effective_from,
            trigger_match=trigger_match,
            trigger_event=trigger_event,
            reason=reason,
            created_by=created_by,
        )
        
        # Automatically activate if effective today
        if effective_from <= date.today():
            suspension.activate()
        
        return suspension

    # ─── Eligibility Checks ────────────────────────────────────────────────────

    @staticmethod
    def is_player_eligible(
        *,
        tenant: Tenant,
        player: Player,
        competition: Competition,
        match: Optional[Match] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Check if a player is eligible to play.
        
        Args:
            tenant: Organization
            player: Player to check
            competition: Competition context
            match: Specific match (optional, for more detailed check)
        
        Returns:
            Tuple of (is_eligible, reason_if_not)
        """
        # Check for active suspensions
        active_suspensions = PlayerSuspension.objects.filter(
            tenant=tenant,
            player=player,
            competition=competition,
            status=PlayerSuspension.SuspensionStatus.ACTIVE,
        ).select_related("competition")
        
        if active_suspensions.exists():
            suspension = active_suspensions.first()
            remaining = suspension.remaining_matches
            return (
                False,
                f"Jogador suspenso por {remaining} jogo(s) — {suspension.get_suspension_type_display()}",
            )
        
        # Check for pending suspensions that should be active
        pending_suspensions = PlayerSuspension.objects.filter(
            tenant=tenant,
            player=player,
            competition=competition,
            status=PlayerSuspension.SuspensionStatus.PENDING,
            effective_from__lte=date.today(),
        )
        
        for suspension in pending_suspensions:
            suspension.activate()
            return (
                False,
                f"Jogador suspenso por {suspension.remaining_matches} jogo(s) — {suspension.get_suspension_type_display()}",
            )
        
        return (True, None)

    @staticmethod
    def get_active_suspensions_for_player(
        *,
        tenant: Tenant,
        player: Player,
        competition: Optional[Competition] = None
    ) -> list[PlayerSuspension]:
        """Get all active suspensions for a player."""
        qs = PlayerSuspension.objects.filter(
            tenant=tenant,
            player=player,
            status=PlayerSuspension.SuspensionStatus.ACTIVE,
        ).select_related("competition", "club")
        
        if competition:
            qs = qs.filter(competition=competition)
        
        return list(qs)

    @staticmethod
    def get_suspended_players_for_competition(
        *,
        tenant: Tenant,
        competition: Competition
    ) -> list[dict]:
        """
        Get all currently suspended players for a competition.
        
        Returns:
            List of dicts with player info and suspension details
        """
        suspensions = PlayerSuspension.objects.filter(
            tenant=tenant,
            competition=competition,
            status=PlayerSuspension.SuspensionStatus.ACTIVE,
        ).select_related("player", "club")
        
        return [
            {
                "player_id": str(s.player.id),
                "player_name": s.player.full_name,
                "club_id": str(s.club.id),
                "club_name": s.club.name,
                "suspension_type": s.suspension_type,
                "suspension_type_display": s.get_suspension_type_display(),
                "matches_remaining": s.remaining_matches,
                "effective_from": s.effective_from,
            }
            for s in suspensions
        ]

    # ─── Suspension Serving ────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def process_match_for_suspensions(
        *,
        tenant: Tenant,
        match: Match
    ) -> list[PlayerSuspension]:
        """
        Process a finished match to update suspension serving.
        
        Called after a match is marked as finished.
        Decrements matches_served for all active suspensions.
        
        Returns:
            List of suspensions that were updated
        """
        if match.status != Match.MatchStatus.FINISHED:
            return []
        
        # Get all active suspensions for players from either club
        home_club_players = PlayerSuspension.objects.filter(
            tenant=tenant,
            club=match.home_club,
            competition=match.competition,
            status=PlayerSuspension.SuspensionStatus.ACTIVE,
        )
        
        away_club_players = PlayerSuspension.objects.filter(
            tenant=tenant,
            club=match.away_club,
            competition=match.competition,
            status=PlayerSuspension.SuspensionStatus.ACTIVE,
        )
        
        updated = []
        
        for suspension in home_club_players | away_club_players:
            suspension.serve_match()
            updated.append(suspension)
        
        return updated

    # ─── Fair Play Rankings ────────────────────────────────────────────────────

    @staticmethod
    def get_fair_play_ranking_for_competition(
        *,
        tenant: Tenant,
        competition: Competition
    ) -> list[dict]:
        """
        Calculate fair play ranking for clubs in a competition.
        
        Ranking is based on:
            - Fewer cards = better ranking
            - Yellow = 1 point, Yellow-red = 3 points, Red = 5 points
        
        Returns:
            List of dicts with club info and fair play score (lower = better)
        """
        from django.db.models import Count, Q, Case, When, IntegerField, Sum
        from clubs.models import Club
        
        # Get all clubs in the competition
        club_ids = Match.objects.filter(
            tenant=tenant,
            competition=competition,
        ).values_list('home_club_id', 'away_club_id').distinct()
        
        club_ids = set()
        for home_id, away_id in Match.objects.filter(
            tenant=tenant,
            competition=competition,
        ).values_list('home_club_id', 'away_club_id'):
            club_ids.add(home_id)
            club_ids.add(away_id)
        
        rankings = []
        
        for club_id in club_ids:
            try:
                club = Club.objects.get(id=club_id)
            except Club.DoesNotExist:
                continue
            
            # Count cards for this club in this competition
            events = MatchEvent.objects.filter(
                tenant=tenant,
                club=club,
                match__competition=competition,
            )
            
            yellows = events.filter(
                event_type=MatchEvent.EventType.YELLOW_CARD
            ).count()
            
            yellow_reds = events.filter(
                event_type=MatchEvent.EventType.YELLOW_RED
            ).count()
            
            reds = events.filter(
                event_type=MatchEvent.EventType.RED_CARD
            ).count()
            
            # Calculate fair play score (lower = better)
            score = (
                yellows * 1 +
                yellow_reds * 3 +
                reds * 5
            )
            
            rankings.append({
                "club_id": str(club.id),
                "club_name": club.name,
                "yellow_cards": yellows,
                "yellow_reds": yellow_reds,
                "red_cards": reds,
                "fair_play_score": score,
            })
        
        # Sort by score (ascending, lower = better)
        rankings.sort(key=lambda x: x["fair_play_score"])
        
        # Add positions
        for i, entry in enumerate(rankings, 1):
            entry["position"] = i
        
        return rankings
