"""
BOLAYETU — Player Document Views

API endpoints for player documents.

Endpoints:
    GET    /api/v1/players/{slug}/documents/           — List player documents
    POST   /api/v1/players/{slug}/documents/           — Upload a document
    GET    /api/v1/players/{slug}/documents/{id}/      — Get document detail
    PATCH  /api/v1/players/{slug}/documents/{id}/      — Update document
    DELETE /api/v1/players/{slug}/documents/{id}/      — Delete document
    POST   /api/v1/players/{slug}/documents/{id}/verify/ — Verify document (admin only)
"""

from drf_spectacular.utils import extend_schema
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.views import APIView

from clubs.models import Club
from common.responses import error_response, success_response
from common.pagination import StandardPagination
from players.models import PlayerDocument
from players.selectors import PlayerSelector
from players.serializers.player_document import (
    PlayerDocumentSerializer,
    PlayerDocumentCreateSerializer,
    PlayerDocumentUpdateSerializer,
    PlayerDocumentVerifySerializer,
)
from players.services.player_document_service import PlayerDocumentService
from players.views.player_media_helpers import (
    player_can_view_all_content,
    player_read_permissions,
    player_write_permission,
    player_write_permissions,
)


class PlayerDocumentListView(APIView):
    """
    GET:  List documents for a player.
    POST: Upload a new document via DAM.
    """

    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return player_read_permissions()
        return player_write_permissions()

    @extend_schema(
        tags=["players"],
        summary="List player documents",
        responses={200: PlayerDocumentSerializer(many=True)},
    )
    def get(self, request, slug: str):
        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        if player_can_view_all_content(request, player):
            documents = player.documents.all()
        else:
            documents = player.documents.filter(
                is_private=False,
                status=PlayerDocument.DocumentStatus.VERIFIED,
            )

        documents = documents.select_related("asset", "club", "uploaded_by", "verified_by")

        paginator = StandardPagination()
        page = paginator.paginate_queryset(documents, request)
        serializer = PlayerDocumentSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        tags=["players"],
        summary="Upload a player document",
        request=PlayerDocumentCreateSerializer,
        responses={201: PlayerDocumentSerializer},
    )
    def post(self, request, slug: str):
        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        permission_error = player_write_permission(request, player)
        if permission_error:
            return permission_error

        serializer = PlayerDocumentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Validation error.",
                errors=serializer.errors,
                status_code=400,
            )

        validated = serializer.validated_data
        club = None
        club_id = validated.get("club")
        if club_id:
            club = Club.objects.filter(id=club_id).first()
            if not club:
                return error_response(message="Club not found.", status_code=400)

        try:
            if validated.get("document"):
                document = PlayerDocumentService.upload_document(
                    player=player,
                    title=validated["title"],
                    category=validated["category"],
                    document=validated["document"],
                    description=validated.get("description", ""),
                    valid_from=validated.get("valid_from"),
                    valid_until=validated.get("valid_until"),
                    club=club,
                    is_private=validated.get("is_private", False),
                    uploaded_by=request.user,
                )
            else:
                document = PlayerDocumentService.create_from_asset(
                    player=player,
                    title=validated["title"],
                    category=validated["category"],
                    asset=validated["asset_instance"],
                    description=validated.get("description", ""),
                    valid_from=validated.get("valid_from"),
                    valid_until=validated.get("valid_until"),
                    club=club,
                    is_private=validated.get("is_private", False),
                    uploaded_by=request.user,
                )
        except ValueError as exc:
            return error_response(message=str(exc), status_code=400)

        result = PlayerDocumentSerializer(document)
        return success_response(
            data=result.data,
            message="Document uploaded successfully.",
            status_code=201,
        )


class PlayerDocumentDetailView(APIView):
    """
    GET:   Get document details.
    PATCH: Update document.
    DELETE: Delete document.
    """

    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return player_read_permissions()
        return player_write_permissions()

    @extend_schema(
        tags=["players"],
        summary="Get player document detail",
        responses={200: PlayerDocumentSerializer},
    )
    def get(self, request, slug: str, document_id: str):
        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        try:
            document = player.documents.select_related(
                "asset", "club", "uploaded_by", "verified_by"
            ).get(id=document_id)
        except PlayerDocument.DoesNotExist:
            return error_response(message="Document not found.", status_code=404)

        if document.is_private and not player_can_view_all_content(request, player):
            return error_response(message="Document not found.", status_code=404)

        if (
            document.status != PlayerDocument.DocumentStatus.VERIFIED
            and not player_can_view_all_content(request, player)
        ):
            return error_response(message="Document not found.", status_code=404)

        serializer = PlayerDocumentSerializer(document)
        return success_response(data=serializer.data)

    @extend_schema(
        tags=["players"],
        summary="Update player document",
        request=PlayerDocumentUpdateSerializer,
        responses={200: PlayerDocumentSerializer},
    )
    def patch(self, request, slug: str, document_id: str):
        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        permission_error = player_write_permission(request, player)
        if permission_error:
            return permission_error

        try:
            document = player.documents.get(id=document_id)
        except PlayerDocument.DoesNotExist:
            return error_response(message="Document not found.", status_code=404)

        serializer = PlayerDocumentUpdateSerializer(
            document, data=request.data, partial=True
        )
        if not serializer.is_valid():
            return error_response(
                message="Validation error.",
                errors=serializer.errors,
                status_code=400,
            )

        serializer.save()
        result = PlayerDocumentSerializer(document)
        return success_response(data=result.data, message="Document updated successfully.")

    @extend_schema(
        tags=["players"],
        summary="Delete player document",
        responses={204: None},
    )
    def delete(self, request, slug: str, document_id: str):
        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        permission_error = player_write_permission(request, player)
        if permission_error:
            return permission_error

        try:
            document = player.documents.get(id=document_id)
        except PlayerDocument.DoesNotExist:
            return error_response(message="Document not found.", status_code=404)

        PlayerDocumentService.remove_document(document=document)
        return success_response(message="Document deleted successfully.")


class PlayerDocumentVerifyView(APIView):
    """
    POST: Verify a document (staff only).
    """

    def get_permissions(self):
        return player_write_permissions()

    @extend_schema(
        tags=["players"],
        summary="Verify player document (admin only)",
        request=PlayerDocumentVerifySerializer,
        responses={200: PlayerDocumentSerializer},
    )
    def post(self, request, slug: str, document_id: str):
        if not request.user.is_staff:
            return error_response(message="Only staff can verify documents.", status_code=403)

        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        try:
            document = player.documents.get(id=document_id)
        except PlayerDocument.DoesNotExist:
            return error_response(message="Document not found.", status_code=404)

        document.verify(request.user)

        serializer = PlayerDocumentSerializer(document)
        return success_response(data=serializer.data, message="Document verified successfully.")
