from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from common.responses import error_response, success_response
from players.models import PlayerPrivacySettings
from players.selectors import PlayerSelector
from players.serializers.player_privacy import PlayerPrivacySettingsSerializer
from players.views.player_media_helpers import player_write_permission


class PlayerPrivacySettingsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["players"],
        summary="Get player privacy settings",
        responses={200: PlayerPrivacySettingsSerializer},
    )
    def get(self, request, slug: str):
        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        permission_error = player_write_permission(request, player)
        if permission_error:
            return permission_error

        settings, _ = PlayerPrivacySettings.objects.get_or_create(player=player)
        return success_response(data=PlayerPrivacySettingsSerializer(settings).data)

    @extend_schema(
        tags=["players"],
        summary="Update player privacy settings",
        request=PlayerPrivacySettingsSerializer,
        responses={200: PlayerPrivacySettingsSerializer},
    )
    def patch(self, request, slug: str):
        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        permission_error = player_write_permission(request, player)
        if permission_error:
            return permission_error

        settings, _ = PlayerPrivacySettings.objects.get_or_create(player=player)
        serializer = PlayerPrivacySettingsSerializer(
            settings,
            data=request.data,
            partial=True,
        )
        if not serializer.is_valid():
            return error_response(message="Validation error.", errors=serializer.errors, status_code=400)

        serializer.save()
        return success_response(
            data=PlayerPrivacySettingsSerializer(settings).data,
            message="Privacy settings updated.",
        )
