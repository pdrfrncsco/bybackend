"""
BOLAYETU — RankingService

Business logic for cross-competition rankings and aggregations.

Key features:
    - Top scorers across all competitions in a season
    - Fair play rankings (clubs and players)
    - Historical club rankings
    - Player global rankings

Rankings are calculated and stored in CompetitionRanking for quick retrieval.
Can be recalculated on-demand or via scheduled tasks.
"""

from django.db import models, transaction
from django.utils import timezone
from datetime import date
from typing import Optional, List
from decimal import Decimal

from core.models import Tenant
from players.models import Player
from clubs.models import Club
from competitions.models import Match, MatchEvent, Competition, CompetitionRanking


class RankingService:
    """
    Handles ranking calculations and aggregations.
    """

    # ─── Top Scorers ───────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def calculate_top_scorers_for_season(
        *,
        tenant: Tenant,
        season: str,
        competition: Optional[Competition] = None
    ) -> List[CompetitionRanking]:
        """
        Calculate and store top scorers ranking for a season.
        
        Args:
            tenant: Organization
            season: Season string (e.g., "2024/2025")
            competition: Optional specific competition (null for all)
        
        Returns:
            List of created/updated CompetitionRanking entries
        """
        from django.db.models import Count, Q, Sum
        
        # Get competitions for the season
        competitions_qs = Competition.objects.filter(tenant=tenant, season=season)
        if competition:
            competitions_qs = competitions_qs.filter(id=competition.id)
        
        # Aggregate goals by player
        players_stats = (
            MatchEvent.objects.filter(
                tenant=tenant,
                match__competition__in=competitions_qs,
                event_type__in=[
                    MatchEvent.EventType.GOAL,
                    MatchEvent.EventType.PENALTY_SCORED,
                ],
            )
            .values(
                "player_id",
                "player__first_name",
                "player__last_name",
                "player__primary_position",
            )
            .annotate(
                goals=Count("id"),
            )
            .filter(player__isnull=False)
            .order_by("-goals")
        )
        
        rankings = []
        previous_goals = None
        position = 0
        position_counter = 0
        
        for stat in players_stats:
            position_counter += 1
            
            # Handle ties (same goals = same position)
            if stat["goals"] != previous_goals:
                position = position_counter
                previous_goals = stat["goals"]
            
            player = Player.objects.get(id=stat["player_id"])
            
            # Get club (most recent registration in competition)
            club = RankingService._get_player_club_for_season(
                player=player,
                tenant=tenant,
                season=season
            )
            
            # Create or update ranking
            ranking, created = CompetitionRanking.objects.update_or_create(
                tenant=tenant,
                ranking_type=CompetitionRanking.RankingType.TOP_SCORER,
                aggregation_level=CompetitionRanking.AggregationLevel.SEASON,
                season=season,
                player=player,
                defaults={
                    "competition": competition,
                    "position": position,
                    "value": Decimal(stat["goals"]),
                    "stats": {
                        "goals": stat["goals"],
                        "club_name": club.name if club else None,
                        "position_played": stat["player__primary_position"],
                    },
                },
            )
            
            rankings.append(ranking)
        
        return rankings

    @staticmethod
    def get_top_scorers(
        *,
        tenant: Tenant,
        season: Optional[str] = None,
        competition: Optional[Competition] = None,
        limit: int = 20
    ) -> List[dict]:
        """
        Get top scorers ranking.
        
        Args:
            tenant: Organization
            season: Season filter
            competition: Competition filter
            limit: Max results
        
        Returns:
            List of ranking entries as dicts
        """
        qs = CompetitionRanking.objects.filter(
            tenant=tenant,
            ranking_type=CompetitionRanking.RankingType.TOP_SCORER,
        ).select_related("player", "club")
        
        if season:
            qs = qs.filter(season=season)
        
        if competition:
            qs = qs.filter(competition=competition)
        
        qs = qs.order_by("position")[:limit]
        
        return [
            {
                "position": r.position,
                "player_id": str(r.player.id),
                "player_name": r.player.full_name,
                "goals": int(r.value),
                "club_name": r.stats.get("club_name"),
                "season": r.season,
            }
            for r in qs
        ]

    # ─── Fair Play Rankings ────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def calculate_fair_play_ranking(
        *,
        tenant: Tenant,
        season: str,
        competition: Optional[Competition] = None
    ) -> List[CompetitionRanking]:
        """
        Calculate and store fair play ranking for clubs in a season.
        
        Lower score = better fair play.
        Yellow = 1 point, Yellow-red = 3 points, Red = 5 points.
        """
        from django.db.models import Count, Q
        
        # Get competitions for the season
        competitions_qs = Competition.objects.filter(tenant=tenant, season=season)
        if competition:
            competitions_qs = competitions_qs.filter(id=competition.id)
        
        # Get all clubs that participated
        club_ids = set()
        for home_id, away_id in Match.objects.filter(
            tenant=tenant,
            competition__in=competitions_qs,
        ).values_list('home_club_id', 'away_club_id'):
            club_ids.add(home_id)
            club_ids.add(away_id)
        
        rankings = []
        
        for club_id in club_ids:
            try:
                club = Club.objects.get(id=club_id)
            except Club.DoesNotExist:
                continue
            
            # Count cards
            events = MatchEvent.objects.filter(
                tenant=tenant,
                club=club,
                match__competition__in=competitions_qs,
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
            
            score = yellows * 1 + yellow_reds * 3 + reds * 5
            
            # Create with temporary position (will be updated after sorting)
            ranking, _ = CompetitionRanking.objects.update_or_create(
                tenant=tenant,
                ranking_type=CompetitionRanking.RankingType.FAIR_PLAY_CLUB,
                aggregation_level=CompetitionRanking.AggregationLevel.SEASON,
                season=season,
                club=club,
                defaults={
                    "competition": competition,
                    "position": 999,  # Temporary, will be updated
                    "value": Decimal(score),
                    "stats": {
                        "yellow_cards": yellows,
                        "yellow_reds": yellow_reds,
                        "red_cards": reds,
                    },
                },
            )
            
            rankings.append(ranking)
        
        # Assign positions (lower score = better position)
        rankings.sort(key=lambda r: r.value)
        for i, ranking in enumerate(rankings, 1):
            ranking.position = i
            ranking.save(update_fields=["position"])
        
        return rankings

    # ─── Historical Rankings ────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def calculate_historical_club_ranking(
        *,
        tenant: Tenant
    ) -> List[CompetitionRanking]:
        """
        Calculate historical ranking for clubs based on all-time points.
        
        Uses Standing data to calculate total points across all seasons.
        """
        from competitions.models import Standing
        from django.db.models import Sum
        
        # Aggregate points by club across all standings
        club_points = (
            Standing.objects.filter(tenant=tenant)
            .values("club_id")
            .annotate(total_points=Sum("points"))
            .order_by("-total_points")
        )
        
        rankings = []
        previous_points = None
        position = 0
        position_counter = 0
        
        for stat in club_points:
            position_counter += 1
            
            if stat["total_points"] != previous_points:
                position = position_counter
                previous_points = stat["total_points"]
            
            try:
                club = Club.objects.get(id=stat["club_id"])
            except Club.DoesNotExist:
                continue
            
            ranking, _ = CompetitionRanking.objects.update_or_create(
                tenant=tenant,
                ranking_type=CompetitionRanking.RankingType.HISTORICAL_POINTS,
                aggregation_level=CompetitionRanking.AggregationLevel.ALL_TIME,
                club=club,
                defaults={
                    "position": position,
                    "value": Decimal(stat["total_points"]),
                },
            )
            
            rankings.append(ranking)
        
        return rankings

    # ─── Helper Methods ─────────────────────────────────────────────────────────

    @staticmethod
    def _get_player_club_for_season(
        *,
        player: Player,
        tenant: Tenant,
        season: str
    ) -> Optional[Club]:
        """Get the player's most recent club for a season."""
        # Try to get from PlayerRegistration if available
        try:
            from players.models import PlayerRegistration
            
            registration = PlayerRegistration.objects.filter(
                player=player,
                tenant=tenant,
            ).order_by("-created_at").first()
            
            if registration:
                return registration.club
        except ImportError:
            pass
        
        # Fallback: get club from most recent match event
        recent_event = MatchEvent.objects.filter(
            player=player,
            tenant=tenant,
            match__competition__season=season,
        ).select_related("club").order_by("-created_at").first()
        
        return recent_event.club if recent_event else None

    @staticmethod
    def recalculate_all_rankings(
        *,
        tenant: Tenant,
        season: Optional[str] = None
    ) -> dict:
        """
        Recalculate all rankings for a tenant/season.
        
        Returns:
            Summary of recalculated rankings
        """
        results = {
            "top_scorers": 0,
            "fair_play": 0,
            "historical": 0,
        }
        
        # Top scorers
        top_scorers = RankingService.calculate_top_scorers_for_season(
            tenant=tenant,
            season=season or "",
        )
        results["top_scorers"] = len(top_scorers)
        
        # Fair play
        fair_play = RankingService.calculate_fair_play_ranking(
            tenant=tenant,
            season=season or "",
        )
        results["fair_play"] = len(fair_play)
        
        # Historical
        historical = RankingService.calculate_historical_club_ranking(
            tenant=tenant,
        )
        results["historical"] = len(historical)
        
        return results

    # ─── Query Methods ──────────────────────────────────────────────────────────

    @staticmethod
    def get_ranking(
        *,
        tenant: Tenant,
        ranking_type: str,
        season: Optional[str] = None,
        limit: int = 20
    ) -> List[dict]:
        """
        Get a specific ranking.
        
        Args:
            tenant: Organization
            ranking_type: Type from CompetitionRanking.RankingType
            season: Season filter
            limit: Max results
        
        Returns:
            List of ranking entries
        """
        qs = CompetitionRanking.objects.filter(
            tenant=tenant,
            ranking_type=ranking_type,
        ).select_related("player", "club")
        
        if season:
            qs = qs.filter(season=season)
        
        qs = qs.order_by("position")[:limit]
        
        results = []
        for r in qs:
            if r.player:
                results.append({
                    "position": r.position,
                    "player_id": str(r.player.id),
                    "player_name": r.player.full_name,
                    "value": float(r.value),
                    "stats": r.stats,
                    "season": r.season,
                })
            elif r.club:
                results.append({
                    "position": r.position,
                    "club_id": str(r.club.id),
                    "club_name": r.club.name,
                    "value": float(r.value),
                    "stats": r.stats,
                    "season": r.season,
                })
        
        return results
