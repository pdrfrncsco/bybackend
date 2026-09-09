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

from django.db import models
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
    no_content_response,
    success_response,
)
from media_assets.constants import AssetCategory, AssetVisibility, OwnerType
from media_assets.exceptions import MediaAssetNotFound
from media_assets.models import MediaAsset, MediaUsage
from media_assets.selectors import MediaAssetSelector, MediaUsageSelector
from media_assets.serializers import (
    MediaAssetListSerializer,
    MediaAssetSerializer,
    MediaAssetUploadSerializer,
    MediaUsageCreateSerializer,
    MediaUsageSerializer,
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
    if not user or not user.is_authenticated:
        return False

    if user.is_staff:
        return True

    if asset.tenant_id is None:
        if asset.uploaded_by_id == user.id:
            return True
        # If linked to a player, check if user is that player
        if asset.owner_type == OwnerType.PLAYER:
            try:
                from players.selectors import PlayerSelector

                linked = PlayerSelector.get_for_user(user)
                if linked and str(linked.id) == str(asset.owner_id):
                    return True
            except Exception:
                pass
        return False

    membership = TenantMembership.objects.filter(
        user=user,
        tenant_id=asset.tenant_id,
        is_active=True,
    ).first()
    if not membership:
        return False

    if asset.visibility in (AssetVisibility.PRIVATE, AssetVisibility.INTERNAL):
        return membership.role in ("owner", "admin") or asset.uploaded_by_id == user.id

    return True


def _user_can_delete_asset(*, asset: MediaAsset, user) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.is_staff or asset.uploaded_by_id == user.id:
        return True

    if asset.owner_type == OwnerType.PLAYER:
        try:
            from players.selectors import PlayerSelector

            linked = PlayerSelector.get_for_user(user)
            if linked and str(linked.id) == str(asset.owner_id):
                return True
        except Exception:
            pass

    if asset.tenant_id:
        membership = TenantMembership.objects.filter(
            user=user,
            tenant_id=asset.tenant_id,
            is_active=True,
        ).first()
        if membership and membership.role in ("owner", "admin"):
            return True

    return False


def _get_user_scoped_asset(*, user, asset_id: str) -> MediaAsset:
    asset = MediaAssetSelector.get_by_id(asset_id=asset_id)

    if not asset or not _asset_visible_to_user(asset=asset, user=user):
        raise MediaAssetNotFound()

    return asset


def _owner_belongs_to_tenant(*, owner_type: str, owner_id, tenant, user=None) -> bool:
    if owner_type == OwnerType.ORGANIZATION:
        return bool(tenant and str(owner_id) == str(tenant.id))

    if owner_type == OwnerType.CLUB:
        from clubs.models import Club

        return bool(tenant and Club.objects.filter(id=owner_id, tenant=tenant).exists())

    if owner_type == OwnerType.COMPETITION:
        from competitions.models import Competition

        return bool(tenant and Competition.objects.filter(id=owner_id, tenant=tenant).exists())

    if owner_type == OwnerType.MATCH:
        from competitions.models import Match

        return bool(tenant and Match.objects.filter(id=owner_id, tenant=tenant).exists())

    if owner_type == OwnerType.PLAYER:
        from players.models import Player

        player = Player.objects.filter(id=owner_id).first()
        if not player:
            return False
        if tenant and player.registrations.filter(club__tenant=tenant, status__in=("registered", "loaned")).exists():
            return True
        if user and getattr(player, "user_id", None) == getattr(user, "id", None):
            return True
        if user and getattr(user, "is_staff", False):
            return True
        return False

    if owner_type == OwnerType.SYSTEM:
        return False

    return False


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
        if owner_type == OwnerType.PLAYER:
            from players.models import Player
            from players.permissions import CanManagePlayerProfile

            player = Player.objects.filter(id=owner_id).first()
            if not player:
                return error_response(
                    message="Jogador não encontrado.",
                    status_code=status.HTTP_404_NOT_FOUND,
                )

            if tenant:
                if not _owner_belongs_to_tenant(
                    owner_type=owner_type,
                    owner_id=owner_id,
                    tenant=tenant,
                    user=request.user,
                ):
                    return error_response(
                        message="Jogador não pertence ao tenant autenticado.",
                        status_code=status.HTTP_403_FORBIDDEN,
                    )
            else:
                if not CanManagePlayerProfile.can_manage(user=request.user, player=player):
                    return error_response(
                        message="Sem permissão para carregar ficheiros para este jogador.",
                        status_code=status.HTTP_403_FORBIDDEN,
                    )
        else:
            if not tenant:
                return error_response(
                    message="Sem permissão para carregar ficheiros neste tenant.",
                    status_code=status.HTTP_403_FORBIDDEN,
                )

            if not _owner_belongs_to_tenant(
                owner_type=owner_type,
                owner_id=owner_id,
                tenant=tenant,
                user=request.user,
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

    List media assets scoped to the user or tenant.
    Supports filtering by owner_type, owner_id, asset_type, category, and search query.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["media"],
        summary="List media assets",
        parameters=[
            OpenApiParameter("owner_type", str, description="Filter by owner type (organization, club, player)"),
            OpenApiParameter("owner_id", str, description="Filter by owner UUID"),
            OpenApiParameter("asset_type", str, description="Filter by type (image, video, etc.)"),
            OpenApiParameter("category", str, description="Filter by category (logo, banner, etc.)"),
            OpenApiParameter("q", str, description="Search in asset names"),
        ],
    )
    def get(self, request):
        owner_type = request.query_params.get("owner_type")
        owner_id = request.query_params.get("owner_id")
        asset_type = request.query_params.get("asset_type")
        category = request.query_params.get("category")
        q = request.query_params.get("q")

        # Get the user's tenant
        membership = TenantMembership.objects.filter(user=request.user, is_active=True).select_related("tenant").first()

        if not membership:
            from players.selectors import PlayerSelector

            linked_player = PlayerSelector.get_for_user(request.user)

            if owner_type == OwnerType.PLAYER and owner_id:
                if not (request.user.is_staff or (linked_player and str(linked_player.id) == str(owner_id))):
                    return error_response(
                        message="Sem permissão para aceder aos ficheiros deste jogador.",
                        status_code=status.HTTP_403_FORBIDDEN,
                    )

                assets = MediaAssetSelector.search(
                    owner_type=owner_type,
                    owner_id=owner_id,
                    asset_type=asset_type,
                    category=category,
                    query=q,
                )
            else:
                assets = MediaAssetSelector.search(
                    uploaded_by_id=request.user.id,
                    asset_type=asset_type,
                    category=category,
                    query=q,
                )
                if linked_player:
                    player_assets = MediaAssetSelector.search(
                        owner_type=OwnerType.PLAYER,
                        owner_id=linked_player.id,
                        asset_type=asset_type,
                        category=category,
                        query=q,
                    )
                    assets = (assets | player_assets).distinct().order_by("-created_at")

            paginator = StandardPagination()
            page = paginator.paginate_queryset(assets, request)
            return paginator.get_paginated_response(MediaAssetListSerializer(page, many=True).data)

        tenant_id = membership.tenant_id

        if owner_type and owner_id:
            if not _owner_belongs_to_tenant(
                owner_type=owner_type,
                owner_id=owner_id,
                tenant=membership.tenant,
                user=request.user,
            ):
                paginator = StandardPagination()
                page = paginator.paginate_queryset(MediaAsset.objects.none(), request)
                return paginator.get_paginated_response([])

            assets = MediaAssetSelector.search(
                owner_type=owner_type,
                owner_id=owner_id,
                asset_type=asset_type,
                category=category,
                query=q,
            )
        else:
            assets = MediaAssetSelector.search(
                tenant_id=tenant_id,
                asset_type=asset_type,
                category=category,
                query=q,
            )

        # Non-staff/non-admin members do not see private/internal assets uploaded by others
        if not (request.user.is_staff or membership.role in ("owner", "admin")):
            assets = assets.filter(
                models.Q(visibility=AssetVisibility.PUBLIC) | models.Q(uploaded_by=request.user)
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
        asset = _get_user_scoped_asset(user=request.user, asset_id=asset_id)

        if not _user_can_delete_asset(asset=asset, user=request.user):
            return error_response(
                message="Não tem permissão para eliminar este asset.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

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


class MediaUsageView(APIView):
    """List usages for an owner or link an existing asset to an owner."""

    def get_permissions(self):
        if self.request.method == "GET":
            from rest_framework.permissions import AllowAny
            return [AllowAny()]
        return [IsAuthenticated()]

    @extend_schema(
        tags=["media"],
        summary="List or create media usages",
        parameters=[
            OpenApiParameter("owner_type", str, required=True),
            OpenApiParameter("owner_id", str, required=True),
        ],
        request=MediaUsageCreateSerializer,
        responses=MediaUsageSerializer,
    )
    def get(self, request):
        owner_type = request.query_params.get("owner_type")
        owner_id = request.query_params.get("owner_id")
        if not owner_type or not owner_id:
            return error_response(
                message="owner_type e owner_id são obrigatórios.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user if request.user and request.user.is_authenticated else None
        membership = _get_user_membership(user=user) if user else None
        tenant = membership.tenant if membership else None

        is_owner_public = False
        if owner_type == OwnerType.PLAYER:
            from players.models import Player
            is_owner_public = Player.objects.filter(id=owner_id, is_public=True).exists()
        elif owner_type == OwnerType.CLUB:
            from clubs.models import Club
            is_owner_public = Club.objects.filter(id=owner_id, is_public=True).exists()
        elif owner_type == OwnerType.ORGANIZATION:
            from core.models import Tenant
            is_owner_public = Tenant.objects.filter(id=owner_id, status="active").exists()

        has_tenant_access = False
        if user:
            has_tenant_access = _owner_belongs_to_tenant(
                owner_type=owner_type,
                owner_id=owner_id,
                tenant=tenant,
                user=user,
            )

        if not (is_owner_public or has_tenant_access):
            return error_response(
                message="Owner não encontrado ou sem permissão de acesso.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        usages = MediaUsageSelector.get_all_for_owner(
            owner_type=owner_type,
            owner_id=owner_id,
        )

        if not has_tenant_access:
            usages = usages.filter(asset__visibility=AssetVisibility.PUBLIC)

        paginator = StandardPagination()
        page = paginator.paginate_queryset(usages, request)
        return paginator.get_paginated_response(MediaUsageSerializer(page, many=True).data)

    def post(self, request):
        serializer = MediaUsageCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Dados de associação inválidos.",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        membership = _get_user_membership(user=request.user)
        tenant = membership.tenant if membership else None

        if not _owner_belongs_to_tenant(
            owner_type=data["owner_type"],
            owner_id=data["owner_id"],
            tenant=tenant,
            user=request.user,
        ):
            return error_response(
                message="Owner não pertence ao tenant autenticado.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        asset = MediaAssetSelector.get_by_id(asset_id=data["asset_id"])
        if not asset or not _asset_visible_to_user(asset=asset, user=request.user):
            return error_response(
                message="Asset não encontrado neste tenant.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if asset.tenant_id and membership and asset.tenant_id != membership.tenant_id:
            return error_response(
                message="Asset não pertence ao tenant autenticado.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        usage = MediaUsage.link_for(
            owner_type=data["owner_type"],
            owner_id=data["owner_id"],
            role=data["role"],
            new_asset=asset,
        )
        return created_response(
            data=MediaUsageSerializer(usage).data,
            message="Asset associado com sucesso.",
        )


class MediaUsageDetailView(APIView):
    """Deactivate a media usage without deleting its asset."""

    permission_classes = [IsAuthenticated]

    def delete(self, request, usage_id: str):
        usage = MediaUsage.objects.select_related("asset").filter(id=usage_id).first()
        if not usage:
            return error_response(
                message="Utilização de media não encontrada.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        membership = _get_user_membership(user=request.user)
        tenant = membership.tenant if membership else None

        if not _owner_belongs_to_tenant(
            owner_type=usage.owner_type,
            owner_id=usage.owner_id,
            tenant=tenant,
            user=request.user,
        ):
            return error_response(
                message="Owner não pertence ao tenant autenticado.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        usage.is_active = False
        usage.save(update_fields=["is_active", "updated_at"])
        return no_content_response()
