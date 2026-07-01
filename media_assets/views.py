"""
BOLAYETU — Media Asset API Views

Endpoints:
    POST   /api/v1/media/upload/          — upload a file, create MediaAsset
    GET    /api/v1/media/                 — list assets (tenant-scoped)
    GET    /api/v1/media/<id>/            — retrieve asset detail
    DELETE /api/v1/media/<id>/            — soft-delete asset
    GET    /api/v1/media/<id>/signed-url/ — get temporary signed URL

Architecture (08_MEDIA_STORAGE_ARCHITECTURE.md §25):
    POST   /api/v1/media/upload
    GET    /api/v1/media/{id}
    DELETE /api/v1/media/{id}
    GET    /api/v1/media/{id}/signed-url
"""

import logging

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from common.responses import (
    created_response,
    error_response,
    no_content_response,
    success_response,
)
from media_assets.constants import AssetCategory, AssetVisibility, OwnerType
from media_assets.exceptions import MediaAssetNotFound
from media_assets.models import MediaAsset
from media_assets.selectors import MediaAssetSelector
from media_assets.serializers import (
    MediaAssetListSerializer,
    MediaAssetSerializer,
    MediaAssetUploadSerializer,
)
from media_assets.services import MediaAssetService

logger = logging.getLogger(__name__)


class MediaAssetUploadView(APIView):
    """
    POST /api/v1/media/upload/

    Upload a file and create a MediaAsset record.
    The caller must provide owner_type, owner_id, and role
    to link the asset to an entity via MediaUsage.
    """

    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["media"],
        request=MediaAssetUploadSerializer,
        summary="Upload a media asset",
        description=(
            "Upload a file and create a MediaAsset record linked to an owner entity. "
            "Supported file types: JPEG, PNG, WebP, GIF, SVG, PDF. "
            "After upload, thumbnail variants are generated asynchronously via Celery."
        ),
    )
    def post(self, request):
        file = request.FILES.get("file")

        if not file:
            return error_response(
                message="Nenhum ficheiro enviado.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        owner_type = request.data.get("owner_type", OwnerType.ORGANIZATION)
        owner_id = request.data.get("owner_id")
        role = request.data.get("role", AssetCategory.LOGO)
        name = request.data.get("name", "") or file.name
        tenant_id = request.data.get("tenant_id")

        if not owner_id:
            return error_response(
                message="owner_id é obrigatório.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Resolve tenant
        tenant = None
        if tenant_id:
            from core.models import Tenant
            tenant = Tenant.objects.filter(id=tenant_id).first()

        try:
            asset = MediaAssetService.upload_for_owner(
                file=file,
                owner_type=owner_type,
                owner_id=owner_id,
                role=role,
                name=name,
                tenant=tenant,
                uploaded_by=request.user,
                images_only=False,
            )
        except Exception as exc:
            logger.exception("Media upload failed")
            raise

        return created_response(
            data=MediaAssetSerializer(asset).data,
            message="Ficheiro carregado com sucesso.",
        )


class MediaAssetListView(APIView):
    """
    GET /api/v1/media/

    List media assets for the authenticated user's organization.
    Supports filtering by asset_type, category, and search query.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["media"],
        summary="List media assets",
        parameters=[
            OpenApiParameter("asset_type", str, description="Filter by type (image, video, etc.)"),
            OpenApiParameter("category", str, description="Filter by category (logo, banner, etc.)"),
            OpenApiParameter("q", str, description="Search in asset names"),
        ],
    )
    def get(self, request):
        from accounts.models import TenantMembership

        # Get the user's tenant
        membership = TenantMembership.objects.filter(
            user=request.user, is_active=True
        ).select_related("tenant").first()

        if not membership:
            return success_response(data=[], message="Sem organização.")

        tenant_id = membership.tenant_id

        assets = MediaAssetSelector.search(
            tenant_id=tenant_id,
            asset_type=request.query_params.get("asset_type"),
            category=request.query_params.get("category"),
            query=request.query_params.get("q"),
        )

        return success_response(
            data=MediaAssetListSerializer(assets, many=True).data,
        )


class MediaAssetDetailView(APIView):
    """
    GET /api/v1/media/<id>/
    DELETE /api/v1/media/<id>/
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["media"], summary="Retrieve a media asset")
    def get(self, request, asset_id: str):
        asset = MediaAssetSelector.get_by_id(asset_id=asset_id)

        if not asset:
            raise MediaAssetNotFound()

        return success_response(
            data=MediaAssetSerializer(asset).data,
        )

    @extend_schema(tags=["media"], summary="Delete a media asset")
    def delete(self, request, asset_id: str):
        try:
            MediaAssetService.delete_asset(asset_id=asset_id)
        except MediaAssetNotFound:
            raise

        return no_content_response()


class MediaAssetSignedUrlView(APIView):
    """
    GET /api/v1/media/<id>/signed-url/

    Generate a temporary pre-signed URL for a private asset.
    Used for content that requires authentication to access.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["media"],
        summary="Get a signed URL for a private media asset",
    )
    def get(self, request, asset_id: str):
        asset = MediaAssetSelector.get_by_id(asset_id=asset_id)

        if not asset:
            raise MediaAssetNotFound()

        if asset.visibility == AssetVisibility.PUBLIC:
            return success_response(
                data={"url": asset.public_url, "is_signed": False},
            )

        from media_assets.storage import get_storage_provider
        provider = get_storage_provider()
        expires_in = int(request.query_params.get("expires_in", 3600))
        signed_url = provider.generate_signed_url(
            object_key=asset.object_key,
            expires_in=expires_in,
        )

        return success_response(
            data={"url": signed_url, "is_signed": True, "expires_in": expires_in},
        )
