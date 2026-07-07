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

from accounts.models import TenantMembership
from common.pagination import StandardPagination
from common.responses import (
    created_response,
    error_response,
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


def _get_user_membership(*, user, tenant_id=None) -> TenantMembership | None:
    memberships = TenantMembership.objects.filter(
        user=user,
        is_active=True,
    ).select_related("tenant")

    if tenant_id:
        memberships = memberships.filter(tenant_id=tenant_id)

    return memberships.first()


def _get_upload_tenant(request, tenant_id=None):
    if tenant_id:
        membership = _get_user_membership(user=request.user, tenant_id=tenant_id)
        return membership.tenant if membership else None

    request_tenant = getattr(request, "tenant", None)
    if request_tenant:
        membership = _get_user_membership(
            user=request.user,
            tenant_id=request_tenant.id,
        )
        if membership:
            return membership.tenant

    membership = _get_user_membership(user=request.user)
    return membership.tenant if membership else None


def _asset_visible_to_user(*, asset: MediaAsset, user) -> bool:
    if asset.tenant_id is None:
        return user.is_staff or asset.uploaded_by_id == user.id

    return TenantMembership.objects.filter(
        user=user,
        tenant_id=asset.tenant_id,
        is_active=True,
    ).exists()


def _get_user_scoped_asset(*, user, asset_id: str) -> MediaAsset:
    asset = MediaAssetSelector.get_by_id(asset_id=asset_id)

    if not asset or not _asset_visible_to_user(asset=asset, user=user):
        raise MediaAssetNotFound()

    return asset


def _owner_belongs_to_tenant(*, owner_type: str, owner_id, tenant) -> bool:
    if owner_type == OwnerType.ORGANIZATION:
        return str(owner_id) == str(tenant.id)

    if owner_type == OwnerType.CLUB:
        from clubs.models import Club

        return Club.objects.filter(id=owner_id, tenant=tenant).exists()

    if owner_type == OwnerType.COMPETITION:
        from competitions.models import Competition

        return Competition.objects.filter(id=owner_id, tenant=tenant).exists()

    if owner_type == OwnerType.MATCH:
        from competitions.models import Match

        return Match.objects.filter(id=owner_id, tenant=tenant).exists()

    if owner_type == OwnerType.SYSTEM:
        return False

    return True


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

        tenant = _get_upload_tenant(request, tenant_id=tenant_id)
        if not tenant:
            return error_response(
                message="Sem permissão para carregar ficheiros neste tenant.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        if not _owner_belongs_to_tenant(
            owner_type=owner_type,
            owner_id=owner_id,
            tenant=tenant,
        ):
            return error_response(
                message="Owner não pertence ao tenant autenticado.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

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
        except Exception:
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
        # Get the user's tenant
        membership = TenantMembership.objects.filter(user=request.user, is_active=True).select_related("tenant").first()

        if not membership:
            paginator = StandardPagination()
            page = paginator.paginate_queryset(MediaAsset.objects.none(), request)
            return paginator.get_paginated_response(MediaAssetListSerializer(page, many=True).data)

        tenant_id = membership.tenant_id

        assets = MediaAssetSelector.search(
            tenant_id=tenant_id,
            asset_type=request.query_params.get("asset_type"),
            category=request.query_params.get("category"),
            query=request.query_params.get("q"),
        )

        paginator = StandardPagination()
        page = paginator.paginate_queryset(assets, request)
        return paginator.get_paginated_response(MediaAssetListSerializer(page, many=True).data)


class MediaAssetDetailView(APIView):
    """
    GET /api/v1/media/<id>/
    DELETE /api/v1/media/<id>/
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["media"], summary="Retrieve a media asset")
    def get(self, request, asset_id: str):
        asset = _get_user_scoped_asset(user=request.user, asset_id=asset_id)

        return success_response(
            data=MediaAssetSerializer(asset).data,
        )

    @extend_schema(tags=["media"], summary="Delete a media asset")
    def delete(self, request, asset_id: str):
        _get_user_scoped_asset(user=request.user, asset_id=asset_id)

        try:
            MediaAssetService.delete_asset(asset_id=asset_id)
        except MediaAssetNotFound:
            raise

        return success_response(message="Asset deleted successfully.")


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
        asset = _get_user_scoped_asset(user=request.user, asset_id=asset_id)

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
