from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView

from common.responses import error_response, success_response
from players.selectors import PlayerSelector
from players.serializers.player_guardian import LegalGuardianSerializer
from players.views.player_media_helpers import (
    player_read_permissions,
    player_write_permissions,
    player_write_permission,
)


class PlayerLegalGuardianListCreateView(APIView):
    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return player_read_permissions()
        return player_write_permissions()

    @extend_schema(
        tags=["players"],
        summary="List legal guardians for player",
        responses={200: LegalGuardianSerializer(many=True)},
    )
    def get(self, request, slug: str):
        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        from players.permissions.player_permissions import CanViewPlayerContact
        can_view = CanViewPlayerContact().has_object_permission(request, self, player)
        if not can_view:
            return error_response(message="Guardians info restricted.", status_code=403)

        guardians = player.legal_guardians.all()
        serializer = LegalGuardianSerializer(guardians, many=True)
        return success_response(data=serializer.data)

    @extend_schema(
        tags=["players"],
        summary="Add legal guardian for player",
        request=LegalGuardianSerializer,
        responses={201: LegalGuardianSerializer},
    )
    def post(self, request, slug: str):
        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        permission_error = player_write_permission(request, player)
        if permission_error:
            return permission_error

        serializer = LegalGuardianSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Validation error.",
                errors=serializer.errors,
                status_code=400,
            )

        guardian = serializer.save(player=player)
        result = LegalGuardianSerializer(guardian)
        return success_response(
            data=result.data,
            message="Legal guardian added.",
            status_code=201,
        )


class PlayerLegalGuardianDetailView(APIView):
    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return player_read_permissions()
        return player_write_permissions()

    @extend_schema(
        tags=["players"],
        summary="Get legal guardian detail",
        responses={200: LegalGuardianSerializer},
    )
    def get(self, request, slug: str, guardian_id):
        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        from players.permissions.player_permissions import CanViewPlayerContact
        can_view = CanViewPlayerContact().has_object_permission(request, self, player)
        if not can_view:
            return error_response(message="Guardians info restricted.", status_code=403)

        try:
            guardian = player.legal_guardians.get(id=guardian_id)
        except Exception:
            return error_response(message="Guardian not found.", status_code=404)

        serializer = LegalGuardianSerializer(guardian)
        return success_response(data=serializer.data)

    @extend_schema(
        tags=["players"],
        summary="Update legal guardian",
        request=LegalGuardianSerializer,
        responses={200: LegalGuardianSerializer},
    )
    def patch(self, request, slug: str, guardian_id):
        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        permission_error = player_write_permission(request, player)
        if permission_error:
            return permission_error

        try:
            guardian = player.legal_guardians.get(id=guardian_id)
        except Exception:
            return error_response(message="Guardian not found.", status_code=404)

        serializer = LegalGuardianSerializer(guardian, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response(
                message="Validation error.",
                errors=serializer.errors,
                status_code=400,
            )

        guardian = serializer.save()
        result = LegalGuardianSerializer(guardian)
        return success_response(
            data=result.data,
            message="Legal guardian updated.",
        )

    @extend_schema(
        tags=["players"],
        summary="Delete legal guardian",
        responses={200: None},
    )
    def delete(self, request, slug: str, guardian_id):
        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        permission_error = player_write_permission(request, player)
        if permission_error:
            return permission_error

        try:
            guardian = player.legal_guardians.get(id=guardian_id)
        except Exception:
            return error_response(message="Guardian not found.", status_code=404)

        guardian.delete()
        return success_response(
            message="Legal guardian deleted.",
            status_code=200,
        )
