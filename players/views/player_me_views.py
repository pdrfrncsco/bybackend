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
        }
        payload = {k: v for k, v in request.data.items() if k in allowed}

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
