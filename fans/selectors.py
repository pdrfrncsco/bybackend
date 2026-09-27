"""
BOLAYETU — Fans App Selectors / Queries
"""

from django.db.models import QuerySet, Q
from competitions.models import Match
from .models import (
    FanProfile,
    FanFollow,
    MatchPrediction,
    FollowTargetType,
    FeedPost,
    FeedPostComment,
)


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

    @staticmethod
    def get_feed_posts(
        user=None,
        category: str | None = None,
        author_type: str | None = None,
        club_id=None,
        player_id=None,
        organization_id=None,
        limit: int = 30,
    ) -> QuerySet[FeedPost]:
        """
        Returns feed posts with related author entities.
        If user follows specific clubs/players and no explicit filter is given,
        it prioritizes followed entities + pinned posts + general official posts.
        """
        qs = FeedPost.objects.select_related(
            "author_user", "club", "player", "organization"
        )

        if category:
            qs = qs.filter(category=category)
        if author_type:
            qs = qs.filter(author_type=author_type)
        if club_id:
            qs = qs.filter(club_id=club_id)
        if player_id:
            qs = qs.filter(player_id=player_id)
        if organization_id:
            qs = qs.filter(organization_id=organization_id)

        # Ordering is handled by Meta: ['-is_pinned', '-created_at']
        return qs[:limit]

    @staticmethod
    def get_post_comments(post_id, limit: int = 50) -> QuerySet[FeedPostComment]:
        """Returns comments for a feed post."""
        return FeedPostComment.objects.filter(
            post_id=post_id,
            is_moderated=False,
        ).select_related("user").order_by("created_at")[:limit]
