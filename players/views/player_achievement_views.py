"""
BOLAYETU — Player Achievement Views

API endpoints for player achievements.

Endpoints:
    GET    /api/v1/players/{slug}/achievements/           — List player achievements
    POST   /api/v1/players/{slug}/achievements/           — Add achievement (staff only)
    GET    /api/v1/players/{slug}/achievements/{id}/      — Get achievement detail
    PATCH  /api/v1/players/{slug}/achievements/{id}/      — Update achievement (staff only)
    DELETE /api/v1/players/{slug}/achievements/{id}/      — Delete achievement (staff only)
    POST   /api/v1/players/{slug}/achievements/{id}/verify/ — Verify achievement (admin only)
"""

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from common.responses import success_response, error_response
from common.pagination import StandardPagination
from players.models import Player, PlayerAchievement
from players.selectors import PlayerSelector
from players.serializers.player_achievement import (
    PlayerAchievementSerializer,
    PlayerAchievementCreateSerializer,
    PlayerAchievementUpdateSerializer,
    PlayerAchievementVerifySerializer,
)
from players.permissions import IsStaffOrReadOnly


class PlayerAchievementListView(APIView):
    """
    GET:  List achievements for a player.
    POST: Add a new achievement (staff only).
    """

    permission_classes = [IsStaffOrReadOnly]

    @extend_schema(
        tags=["players"],
        summary="List player achievements",
        responses={200: PlayerAchievementSerializer(many=True)},
    )
    def get(self, request, slug: str):
        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        achievements = player.achievements.select_related("competition", "club")

        # Optional filters
        achievement_type = request.query_params.get("type")
        if achievement_type:
            achievements = achievements.filter(achievement_type=achievement_type)

        level = request.query_params.get("level")
        if level:
            achievements = achievements.filter(level=level)

        season = request.query_params.get("season")
        if season:
            achievements = achievements.filter(season=season)

        achievements = achievements.order_by("-date_achieved", "-created_at")

        paginator = StandardPagination()
        page = paginator.paginate_queryset(achievements, request)
        serializer = PlayerAchievementSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        tags=["players"],
        summary="Add a player achievement (staff only)",
        request=PlayerAchievementCreateSerializer,
        responses={201: PlayerAchievementSerializer},
    )
    def post(self, request, slug: str):
        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        serializer = PlayerAchievementCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Validation error.",
                errors=serializer.errors,
                status_code=400,
            )

        achievement = PlayerAchievement.objects.create(
            player=player,
            **serializer.validated_data,
        )

        result = PlayerAchievementSerializer(achievement)
        return success_response(
            data=result.data,
            message="Achievement added successfully.",
            status_code=201,
        )


class PlayerAchievementDetailView(APIView):
    """
    GET:   Get achievement details.
    PATCH: Update achievement (staff only).
    DELETE: Delete achievement (staff only).
    """

    permission_classes = [IsStaffOrReadOnly]

    @extend_schema(
        tags=["players"],
        summary="Get player achievement detail",
        responses={200: PlayerAchievementSerializer},
    )
    def get(self, request, slug: str, achievement_id: str):
        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        try:
            achievement = player.achievements.select_related(
                "competition", "club"
            ).get(id=achievement_id)
        except PlayerAchievement.DoesNotExist:
            return error_response(message="Achievement not found.", status_code=404)

        serializer = PlayerAchievementSerializer(achievement)
        return success_response(data=serializer.data)

    @extend_schema(
        tags=["players"],
        summary="Update player achievement (staff only)",
        request=PlayerAchievementUpdateSerializer,
        responses={200: PlayerAchievementSerializer},
    )
    def patch(self, request, slug: str, achievement_id: str):
        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        try:
            achievement = player.achievements.get(id=achievement_id)
        except PlayerAchievement.DoesNotExist:
            return error_response(message="Achievement not found.", status_code=404)

        serializer = PlayerAchievementUpdateSerializer(
            achievement, data=request.data, partial=True
        )
        if not serializer.is_valid():
            return error_response(
                message="Validation error.",
                errors=serializer.errors,
                status_code=400,
            )

        serializer.save()
        result = PlayerAchievementSerializer(achievement)
        return success_response(data=result.data, message="Achievement updated successfully.")

    @extend_schema(
        tags=["players"],
        summary="Delete player achievement (staff only)",
        responses={204: None},
    )
    def delete(self, request, slug: str, achievement_id: str):
        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        try:
            achievement = player.achievements.get(id=achievement_id)
        except PlayerAchievement.DoesNotExist:
            return error_response(message="Achievement not found.", status_code=404)

        achievement.delete()
        return success_response(message="Achievement deleted successfully.")


class PlayerAchievementVerifyView(APIView):
    """
    POST: Verify an achievement (admin only).
    """

    permission_classes = [IsStaffOrReadOnly]

    @extend_schema(
        tags=["players"],
        summary="Verify player achievement (admin only)",
        request=PlayerAchievementVerifySerializer,
        responses={200: PlayerAchievementSerializer},
    )
    def post(self, request, slug: str, achievement_id: str):
        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        try:
            achievement = player.achievements.get(id=achievement_id)
        except PlayerAchievement.DoesNotExist:
            return error_response(message="Achievement not found.", status_code=404)

        achievement.is_verified = True
        achievement.save(update_fields=["is_verified"])

        serializer = PlayerAchievementSerializer(achievement)
        return success_response(data=serializer.data, message="Achievement verified successfully.")
