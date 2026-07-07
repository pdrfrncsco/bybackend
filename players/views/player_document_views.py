"""
BOLAYETU — Player Document Views

API endpoints for player documents.

Endpoints:
    GET    /api/v1/players/{slug}/documents/           — List player documents
    POST   /api/v1/players/{slug}/documents/           — Upload a document (staff only)
    GET    /api/v1/players/{slug}/documents/{id}/      — Get document detail
    PATCH  /api/v1/players/{slug}/documents/{id}/      — Update document (staff only)
    DELETE /api/v1/players/{slug}/documents/{id}/      — Delete document (staff only)
    POST   /api/v1/players/{slug}/documents/{id}/verify/ — Verify document (admin only)
"""

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from common.responses import success_response, error_response
from common.pagination import StandardPagination
from players.models import Player, PlayerDocument
from players.selectors import PlayerSelector
from players.serializers.player_document import (
    PlayerDocumentSerializer,
    PlayerDocumentCreateSerializer,
    PlayerDocumentUpdateSerializer,
    PlayerDocumentVerifySerializer,
)
from players.permissions import IsStaffOrReadOnly


class PlayerDocumentListView(APIView):
    """
    GET:  List documents for a player.
    POST: Upload a new document (staff only).
    """

    permission_classes = [IsStaffOrReadOnly]

    @extend_schema(
        tags=["players"],
        summary="List player documents",
        responses={200: PlayerDocumentSerializer(many=True)},
    )
    def get(self, request, slug: str):
        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        # Filter by visibility based on user permissions
        if request.user.is_authenticated and request.user.is_staff:
            documents = player.documents.all()
        else:
            # Public users only see non-private, verified documents
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
        summary="Upload a player document (staff only)",
        request=PlayerDocumentCreateSerializer,
        responses={201: PlayerDocumentSerializer},
    )
    def post(self, request, slug: str):
        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        serializer = PlayerDocumentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Validation error.",
                errors=serializer.errors,
                status_code=400,
            )

        document = PlayerDocument.objects.create(
            player=player,
            uploaded_by=request.user,
            **serializer.validated_data,
        )

        result = PlayerDocumentSerializer(document)
        return success_response(
            data=result.data,
            message="Document uploaded successfully.",
            status_code=201,
        )


class PlayerDocumentDetailView(APIView):
    """
    GET:   Get document details.
    PATCH: Update document (staff only).
    DELETE: Delete document (staff only).
    """

    permission_classes = [IsStaffOrReadOnly]

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

        # Check visibility permissions
        if document.is_private and not (
            request.user.is_authenticated and request.user.is_staff
        ):
            return error_response(message="Document not found.", status_code=404)

        serializer = PlayerDocumentSerializer(document)
        return success_response(data=serializer.data)

    @extend_schema(
        tags=["players"],
        summary="Update player document (staff only)",
        request=PlayerDocumentUpdateSerializer,
        responses={200: PlayerDocumentSerializer},
    )
    def patch(self, request, slug: str, document_id: str):
        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

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
        summary="Delete player document (staff only)",
        responses={204: None},
    )
    def delete(self, request, slug: str, document_id: str):
        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        try:
            document = player.documents.get(id=document_id)
        except PlayerDocument.DoesNotExist:
            return error_response(message="Document not found.", status_code=404)

        document.delete()
        return success_response(message="Document deleted successfully.")


class PlayerDocumentVerifyView(APIView):
    """
    POST: Verify a document (admin only).
    """

    permission_classes = [IsStaffOrReadOnly]

    @extend_schema(
        tags=["players"],
        summary="Verify player document (admin only)",
        request=PlayerDocumentVerifySerializer,
        responses={200: PlayerDocumentSerializer},
    )
    def post(self, request, slug: str, document_id: str):
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
