"""
Player self-service views for authenticated users with a linked profile.
"""

from drf_spectacular.utils import extend_schema
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from common.responses import error_response, success_response
from players.permissions import CanManagePlayerProfile
from players.selectors import PlayerSelector
from players.serializers import PlayerDetailSerializer, PlayerSerializer
from players.services import NoPlayerProfile, PlayerService


class PlayerOnboardingStatusView(APIView):
    """
    Return onboarding gate status for the authenticated user's player profile.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["players"])
    def get(self, request):
        try:
            player = PlayerService.get_player_for_user(request.user)
        except NoPlayerProfile:
            return success_response(
                data={
                    "onboarding_required": True,
                    "has_player_profile": False,
                    "has_basic_info": False,
                    "has_football_info": False,
                    "next_step": "profile",
                    "player": None,
                },
                message="Player onboarding status retrieved successfully.",
            )

        has_basic_info = bool(
            player.first_name
            and player.last_name
            and player.date_of_birth
            and player.nationality
        )
        has_football_info = bool(player.primary_position and player.primary_position != "multiple")
        onboarding_required = not (has_basic_info and has_football_info)
        next_step = None
        if not has_basic_info:
            next_step = "profile"
        elif not has_football_info:
            next_step = "football"

        return success_response(
            data={
                "onboarding_required": onboarding_required,
                "has_player_profile": True,
                "has_basic_info": has_basic_info,
                "has_football_info": has_football_info,
                "next_step": next_step,
                "player": PlayerSerializer(player).data,
            },
            message="Player onboarding status retrieved successfully.",
        )


class PlayerMeView(APIView):
    """
    GET/PATCH /api/v1/players/me/

    Retrieve or update the authenticated user's linked player profile.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["players"],
        summary="Get my player profile",
        responses={200: PlayerDetailSerializer},
    )
    def get(self, request):
        try:
            player = PlayerService.get_player_for_user(request.user)
        except NoPlayerProfile:
            return error_response(message="No player profile linked to this account.", status_code=404)

        serializer = PlayerDetailSerializer(player)
        return success_response(data=serializer.data, message="Player profile retrieved successfully.")

    @extend_schema(
        tags=["players"],
        summary="Update my player profile",
        description="""
        Update player profile fields.
        
        DEPRECATION NOTICE:
        - 'email' and 'phone' fields are deprecated. Use PATCH /api/v1/players/{id}/contacts/ instead.
        
        Compatibility window: 2 sprints (ends September 2026).
        """,
        request=PlayerSerializer,
        responses={200: PlayerSerializer},
    )
    def patch(self, request):
        try:
            player = PlayerService.get_player_for_user(request.user)
        except NoPlayerProfile:
            return error_response(message="No player profile linked to this account.", status_code=404)

        allowed = {
            "first_name",
            "last_name",
            "date_of_birth",
            "nationality",
            "primary_position",
            "email",
            "phone",
            "height_cm",
            "weight_kg",
            "foot",
            "bio",
            "is_public",
        }
        payload = {k: v for k, v in request.data.items() if k in allowed}

        # Coerce date_of_birth string (e.g. "1995-05-15") → date object
        if "date_of_birth" in payload and isinstance(payload["date_of_birth"], str):
            from datetime import date as _date
            try:
                payload["date_of_birth"] = _date.fromisoformat(payload["date_of_birth"])
            except ValueError:
                return error_response(
                    message="Invalid date_of_birth format. Expected YYYY-MM-DD.",
                    status_code=400,
                )

        try:
            player = PlayerService.update_player(player, **payload)
        except Exception as exc:
            return error_response(message=str(exc), status_code=400)

        serializer = PlayerSerializer(player)
        return success_response(data=serializer.data, message="Player profile updated successfully.")


class PlayerAvatarView(APIView):
    """
    POST /api/v1/players/me/avatar/
    POST /api/v1/players/{slug}/avatar/
    """

    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated, CanManagePlayerProfile]

    def _resolve_player(self, request, slug: str | None):
        if slug:
            player = PlayerSelector.get_by_slug(slug)
            if not player:
                return None, error_response(message="Player not found.", status_code=404)
            if not CanManagePlayerProfile.can_manage(user=request.user, player=player):
                return None, error_response(message="You do not have permission to manage this player.", status_code=403)
            return player, None

        try:
            return PlayerService.get_player_for_user(request.user), None
        except NoPlayerProfile:
            return None, error_response(message="No player profile linked to this account.", status_code=404)

    @extend_schema(
        tags=["players"],
        summary="Upload player avatar",
        description="""
        Upload a player avatar image.
        
        This endpoint creates/updates:
        - profile_photo: MediaAsset FK (preferred, new)
        - avatar: URL field (deprecated, for backwards compatibility)
        
        Use profile_photo_url property to get current photo URL (prefers asset, falls back to URL).
        
        Compatibility window: 2 sprints (ends September 2026). After that, avatar URL field will be removed.
        """,
        responses={200: PlayerSerializer},
    )
    def post(self, request, slug: str | None = None):
        player, error = self._resolve_player(request, slug)
        if error:
            return error

        file = request.FILES.get("avatar")
        if not file:
            return error_response(message="No avatar file provided.", status_code=400)

        try:
            player = PlayerService.upload_avatar(player=player, file=file, uploaded_by=request.user)
        except ValueError as exc:
            return error_response(message=str(exc), status_code=400)
        except Exception as exc:
            return error_response(message=str(exc), status_code=400)

        serializer = PlayerSerializer(player)
        return success_response(data=serializer.data, message="Avatar uploaded successfully.")
