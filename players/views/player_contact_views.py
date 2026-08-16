from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView

from common.responses import error_response, success_response
from players.selectors import PlayerSelector
from players.serializers.player_contact import PlayerContactSerializer, EmergencyContactSerializer
from players.services.player_contact_service import PlayerContactService
from players.views.player_media_helpers import player_read_permissions, player_write_permissions, player_write_permission


class PlayerContactView(APIView):
    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return player_read_permissions()
        return player_write_permissions()

    @extend_schema(tags=["players"], summary="Get player contact info", responses={200: PlayerContactSerializer})
    def get(self, request, slug: str):
        # Onboarding and self-service pages can hit this endpoint before the
        # player profile is public, so resolve by slug and let permissions decide.
        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        from players.permissions.player_permissions import CanViewPlayerContact

        contact = getattr(player, "contact", None)
        if not contact:
            return success_response(data=None, message="No contact info.")

        # Enforce privacy for contact info
        can_view_contact = CanViewPlayerContact().has_object_permission(request, self, player)
        if not can_view_contact:
            return error_response(message="Contact not found.", status_code=404)

        serializer = PlayerContactSerializer(contact)
        return success_response(data=serializer.data)

    @extend_schema(tags=["players"], summary="Update player contact info", request=PlayerContactSerializer, responses={200: PlayerContactSerializer})
    def patch(self, request, slug: str):
        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        permission_error = player_write_permission(request, player)
        if permission_error:
            return permission_error

        serializer = PlayerContactSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response(message="Validation error.", errors=serializer.errors, status_code=400)

        contact = PlayerContactService.upsert_contact(player=player, data=serializer.validated_data)
        result = PlayerContactSerializer(contact)
        return success_response(data=result.data, message="Contact updated.")


class PlayerEmergencyContactListCreateView(APIView):
    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return player_read_permissions()
        return player_write_permissions()

    @extend_schema(tags=["players"], summary="List emergency contacts", responses={200: EmergencyContactSerializer(many=True)})
    def get(self, request, slug: str):
        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        from players.permissions.player_permissions import CanViewPlayerContact

        contacts = player.emergency_contacts.all()

        # Emergency contacts considered contact info; restrict by contact_visibility
        can_view_contact = CanViewPlayerContact().has_object_permission(request, self, player)
        if not can_view_contact:
            return error_response(message="Contact not found.", status_code=404)

        serializer = EmergencyContactSerializer(contacts, many=True)
        return success_response(data=serializer.data)

    @extend_schema(tags=["players"], summary="Add emergency contact", request=EmergencyContactSerializer, responses={201: EmergencyContactSerializer})
    def post(self, request, slug: str):
        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        permission_error = player_write_permission(request, player)
        if permission_error:
            return permission_error

        serializer = EmergencyContactSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(message="Validation error.", errors=serializer.errors, status_code=400)

        contact = serializer.save(player=player)
        result = EmergencyContactSerializer(contact)
        return success_response(data=result.data, message="Emergency contact added.", status_code=201)
