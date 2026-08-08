from drf_spectacular.utils import extend_schema
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.views import APIView

from common.responses import error_response, success_response
from common.pagination import StandardPagination
from players.selectors import PlayerSelector
from players.serializers.player_identity import (
    PlayerIdentityDocumentSerializer,
    PlayerIdentityDocumentCreateSerializer,
    PlayerIdentityDocumentUpdateSerializer,
)
from players.services.player_identity_service import PlayerIdentityService
from players.views.player_media_helpers import (
    player_can_view_all_content,
    player_read_permissions,
    player_write_permissions,
    player_write_permission,
)


class PlayerIdentityDocumentListView(APIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return player_read_permissions()
        return player_write_permissions()

    @extend_schema(tags=["players"], summary="List player identity documents", responses={200: PlayerIdentityDocumentSerializer(many=True)})
    def get(self, request, slug: str):
        player = PlayerSelector.get_public_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        if player_can_view_all_content(request, player):
            docs = player.identity_documents.all()
        else:
            docs = player.identity_documents.filter(verification_status="verified")

        paginator = StandardPagination()
        page = paginator.paginate_queryset(docs, request)
        serializer = PlayerIdentityDocumentSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(tags=["players"], summary="Upload identity document", request=PlayerIdentityDocumentCreateSerializer, responses={201: PlayerIdentityDocumentSerializer})
    def post(self, request, slug: str):
        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        permission_error = player_write_permission(request, player)
        if permission_error:
            return permission_error

        serializer = PlayerIdentityDocumentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(message="Validation error.", errors=serializer.errors, status_code=400)

        validated = serializer.validated_data
        try:
            doc = PlayerIdentityService.create_document(player=player, validated_data=validated, uploaded_by=request.user)
        except ValueError as exc:
            return error_response(message=str(exc), status_code=400)

        result = PlayerIdentityDocumentSerializer(doc)
        return success_response(data=result.data, message="Identity document uploaded.", status_code=201)


class PlayerIdentityDocumentDetailView(APIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return player_read_permissions()
        return player_write_permissions()

    @extend_schema(tags=["players"], summary="Get identity document detail", responses={200: PlayerIdentityDocumentSerializer})
    def get(self, request, slug: str, document_id: str):
        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        try:
            doc = player.identity_documents.get(id=document_id)
        except Exception:
            return error_response(message="Document not found.", status_code=404)

        if doc.verification_status != "verified" and not player_can_view_all_content(request, player):
            return error_response(message="Document not found.", status_code=404)

        serializer = PlayerIdentityDocumentSerializer(doc)
        return success_response(data=serializer.data)

    @extend_schema(tags=["players"], summary="Update identity document", request=PlayerIdentityDocumentUpdateSerializer, responses={200: PlayerIdentityDocumentSerializer})
    def patch(self, request, slug: str, document_id: str):
        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        permission_error = player_write_permission(request, player)
        if permission_error:
            return permission_error

        try:
            doc = player.identity_documents.get(id=document_id)
        except Exception:
            return error_response(message="Document not found.", status_code=404)

        serializer = PlayerIdentityDocumentUpdateSerializer(doc, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response(message="Validation error.", errors=serializer.errors, status_code=400)

        PlayerIdentityService.update_document(document=doc, data=serializer.validated_data)
        result = PlayerIdentityDocumentSerializer(doc)
        return success_response(data=result.data, message="Document updated.")

    @extend_schema(tags=["players"], summary="Delete identity document", responses={204: None})
    def delete(self, request, slug: str, document_id: str):
        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        permission_error = player_write_permission(request, player)
        if permission_error:
            return permission_error

        try:
            doc = player.identity_documents.get(id=document_id)
        except Exception:
            return error_response(message="Document not found.", status_code=404)

        PlayerIdentityService.remove_document(document=doc)
        return success_response(message="Document deleted.")


class PlayerIdentityDocumentVerifyView(APIView):
    def get_permissions(self):
        return player_write_permissions()

    @extend_schema(tags=["players"], summary="Verify identity document (staff only)", responses={200: PlayerIdentityDocumentSerializer})
    def post(self, request, slug: str, document_id: str):
        if not request.user or not request.user.is_staff:
            return error_response(message="Only staff can verify documents.", status_code=403)

        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        try:
            doc = player.identity_documents.get(id=document_id)
        except Exception:
            return error_response(message="Document not found.", status_code=404)

        PlayerIdentityService.verify_document(document=doc, verified_by=request.user)
        serializer = PlayerIdentityDocumentSerializer(doc)
        return success_response(data=serializer.data, message="Document verified.")
