"""
BOLAYETU — Fans App Selectors / Queries
"""

from django.db.models import QuerySet, Q
from competitions.models import Match
from .models import FanProfile, FanFollow, MatchPrediction, FollowTargetType


class FanSelector:
    """Read queries for fan features."""

    @staticmethod
    def get_user_follows(user, target_type: str | None = None) -> QuerySet[FanFollow]:
        qs = FanFollow.objects.filter(user=user).select_related("club", "player", "competition")
        if target_type:
            qs = qs.filter(target_type=target_type)
        return qs.order_by("-created_at")

    @staticmethod
    def get_upcoming_matches_for_fan(user, limit: int = 10) -> QuerySet[Match]:
        """
        Returns upcoming matches that involve clubs or competitions the user follows.
        """
        followed_club_ids = FanFollow.objects.filter(
            user=user, target_type=FollowTargetType.CLUB, club__isnull=False
        ).values_list("club_id", flat=True)

        followed_comp_ids = FanFollow.objects.filter(
            user=user, target_type=FollowTargetType.COMPETITION, competition__isnull=False
        ).values_list("competition_id", flat=True)

        query = Q()
        if followed_club_ids:
            query |= Q(home_club_id__in=followed_club_ids) | Q(away_club_id__in=followed_club_ids)
        if followed_comp_ids:
            query |= Q(competition_id__in=followed_comp_ids)

        if not query:
            # Fallback to general upcoming matches
            return Match.objects.filter(
                status__in=["scheduled", "live", "first_half", "second_half"]
            ).select_related("home_club", "away_club", "competition").order_by("match_date")[:limit]

        return Match.objects.filter(query).filter(
            status__in=["scheduled", "live", "first_half", "second_half"]
        ).select_related("home_club", "away_club", "competition").order_by("match_date")[:limit]

    @staticmethod
    def get_user_predictions(user) -> QuerySet[MatchPrediction]:
        return MatchPrediction.objects.filter(user=user).select_related(
            "match", "match__competition", "match__home_club", "match__away_club"
        ).order_by("-created_at")

    @staticmethod
    def get_leaderboard(limit: int = 25) -> QuerySet[FanProfile]:
        """Returns top fans ordered by prediction points."""
        return FanProfile.objects.select_related("user", "favorite_club").order_by(
            "-points", "-correct_predictions_count", "created_at"
        )[:limit]
