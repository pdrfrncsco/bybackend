"""
BOLAYETU — Player Achievement Views

API endpoints for player achievements.

Endpoints:
    GET    /api/v1/players/{slug}/achievements/           — List player achievements
    POST   /api/v1/players/{slug}/achievements/           — Add achievement
    GET    /api/v1/players/{slug}/achievements/{id}/      — Get achievement detail
    PATCH  /api/v1/players/{slug}/achievements/{id}/      — Update achievement
    DELETE /api/v1/players/{slug}/achievements/{id}/      — Delete achievement
    POST   /api/v1/players/{slug}/achievements/{id}/verify/ — Verify achievement (admin only)
"""

from drf_spectacular.utils import extend_schema
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.views import APIView

from clubs.models import Club
from common.responses import error_response, success_response
from common.pagination import StandardPagination
from competitions.models import Competition
from players.models import PlayerAchievement
from players.selectors import PlayerSelector
from players.serializers.player_achievement import (
    PlayerAchievementSerializer,
    PlayerAchievementCreateSerializer,
    PlayerAchievementUpdateSerializer,
    PlayerAchievementVerifySerializer,
)
from players.services.player_achievement_service import PlayerAchievementService
from players.views.player_media_helpers import (
    player_read_permissions,
    player_write_permission,
    player_write_permissions,
)


class PlayerAchievementListView(APIView):
    """
    GET:  List achievements for a player.
    POST: Add a new achievement with optional DAM media uploads.
    """

    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return player_read_permissions()
        return player_write_permissions()

    @extend_schema(
        tags=["players"],
        summary="List player achievements",
        responses={200: PlayerAchievementSerializer(many=True)},
    )
    def get(self, request, slug: str):
        player = PlayerSelector.get_public_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        achievements = player.achievements.select_related(
            "competition", "club", "trophy_asset", "certificate_asset"
        )

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
        summary="Add a player achievement",
        request=PlayerAchievementCreateSerializer,
        responses={201: PlayerAchievementSerializer},
    )
    def post(self, request, slug: str):
        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        permission_error = player_write_permission(request, player)
        if permission_error:
            return permission_error

        serializer = PlayerAchievementCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Validation error.",
                errors=serializer.errors,
                status_code=400,
            )

        validated = serializer.validated_data
        competition = None
        club = None

        competition_id = validated.get("competition")
        if competition_id:
            competition = Competition.objects.filter(id=competition_id).first()
            if not competition:
                return error_response(message="Competition not found.", status_code=400)

        club_id = validated.get("club")
        if club_id:
            club = Club.objects.filter(id=club_id).first()
            if not club:
                return error_response(message="Club not found.", status_code=400)

        try:
            achievement = PlayerAchievementService.create_achievement(
                player=player,
                title=validated["title"],
                achievement_type=validated["achievement_type"],
                level=validated["level"],
                description=validated.get("description", ""),
                date_achieved=validated.get("date_achieved"),
                season=validated.get("season", ""),
                competition=competition,
                club=club,
                trophy_image_file=validated.get("trophy_image"),
                certificate_file=validated.get("certificate"),
                trophy_image_url=validated.get("trophy_image_url", ""),
                certificate_url=validated.get("certificate_url", ""),
                stats_snapshot=validated.get("stats_snapshot"),
                uploaded_by=request.user,
            )
        except ValueError as exc:
            return error_response(message=str(exc), status_code=400)

        result = PlayerAchievementSerializer(achievement)
        return success_response(
            data=result.data,
            message="Achievement added successfully.",
            status_code=201,
        )


class PlayerAchievementDetailView(APIView):
    """
    GET:   Get achievement details.
    PATCH: Update achievement.
    DELETE: Delete achievement.
    """

    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return player_read_permissions()
        return player_write_permissions()

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
                "competition", "club", "trophy_asset", "certificate_asset"
            ).get(id=achievement_id)
        except PlayerAchievement.DoesNotExist:
            return error_response(message="Achievement not found.", status_code=404)

        serializer = PlayerAchievementSerializer(achievement)
        return success_response(data=serializer.data)

    @extend_schema(
        tags=["players"],
        summary="Update player achievement",
        request=PlayerAchievementUpdateSerializer,
        responses={200: PlayerAchievementSerializer},
    )
    def patch(self, request, slug: str, achievement_id: str):
        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        permission_error = player_write_permission(request, player)
        if permission_error:
            return permission_error

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
        summary="Delete player achievement",
        responses={204: None},
    )
    def delete(self, request, slug: str, achievement_id: str):
        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        permission_error = player_write_permission(request, player)
        if permission_error:
            return permission_error

        try:
            achievement = player.achievements.get(id=achievement_id)
        except PlayerAchievement.DoesNotExist:
            return error_response(message="Achievement not found.", status_code=404)

        PlayerAchievementService.remove_achievement(achievement=achievement)
        return success_response(message="Achievement deleted successfully.")


class PlayerAchievementVerifyView(APIView):
    """
    POST: Verify an achievement (staff only).
    """

    def get_permissions(self):
        return player_write_permissions()

    @extend_schema(
        tags=["players"],
        summary="Verify player achievement (admin only)",
        request=PlayerAchievementVerifySerializer,
        responses={200: PlayerAchievementSerializer},
    )
    def post(self, request, slug: str, achievement_id: str):
        if not request.user.is_staff:
            return error_response(message="Only staff can verify achievements.", status_code=403)

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
