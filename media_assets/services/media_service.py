"""
BOLAYETU — Media Asset Service

Handles all business logic for file uploads, metadata management,
asset linking (MediaUsage), and deletion.

Architecture (08A_DIGITAL_ASSET_MANAGEMENT.md):
    - This service is the SINGLE entry point for all file operations.
    - Domain modules (organizations, clubs, competitions, etc.) MUST
      call this service instead of handling file storage themselves.
    - The service uses StorageProvider to abstract the backend.
    - After upload, a Celery task is queued to generate thumbnails.

Rules:
    - Never store file paths directly in domain models.
    - Always create a MediaAsset + MediaUsage pair.
    - Wrap all DB mutations in @transaction.atomic.
"""

import logging
import os
import uuid

from django.conf import settings
from django.db import transaction

from media_assets.constants import (
    AssetCategory,
    AssetStatus,
    AssetType,
    AssetVisibility,
    OwnerType,
)
from media_assets.exceptions import (
    MediaAssetNotFound,
    MediaAssetUploadFailed,
    MediaUsageNotFound,
)
from media_assets.models import MediaAsset, MediaUsage
from media_assets.storage import get_storage_provider
from media_assets.validators import validate_image_upload, validate_upload

logger = logging.getLogger(__name__)


class MediaAssetService:
    """
    Central service for all Digital Asset Management operations.

    Usage examples:
        # Upload a logo for an organization
        asset = MediaAssetService.upload_for_owner(
            file=request.FILES["logo"],
            owner_type=OwnerType.ORGANIZATION,
            owner_id=tenant.id,
            role=AssetCategory.LOGO,
            name=f"{tenant.name} Logo",
            tenant=tenant,
            uploaded_by=request.user,
        )

        # Get the current logo for an organization
        usage = MediaUsage.get_active_for(
            owner_type=OwnerType.ORGANIZATION,
            owner_id=tenant.id,
            role=AssetCategory.LOGO,
        )
        logo_url = usage.asset.public_url if usage else None
    """

    @staticmethod
    def _build_object_key(
        *,
        owner_type: str,
        owner_id,
        role: str,
        file_uuid: str,
        extension: str,
        tenant_slug: str | None = None,
    ) -> str:
        """
        Build the storage object key following the directory structure
        defined in 08_MEDIA_STORAGE_ARCHITECTURE.md §7.

        Format:
            tenant/<slug>/<domain>/<role>/<uuid>.<ext>
        or for system assets:
            system/<role>/<uuid>.<ext>
        """
        ext_part = f".{extension}" if extension else ""
        filename = f"{file_uuid}{ext_part}"

        if tenant_slug:
            return f"tenant/{tenant_slug}/{owner_type}/{role}/{filename}"
        return f"system/{owner_type}/{role}/{filename}"

    @staticmethod
    @transaction.atomic
    def upload_for_owner(
        *,
        file,
        owner_type: str,
        owner_id,
        role: str,
        name: str,
        tenant=None,
        uploaded_by=None,
        visibility: str = AssetVisibility.PUBLIC,
        images_only: bool = False,
    ) -> MediaAsset:
        """
        Upload a file, create a MediaAsset record, and link it to the owner
        via MediaUsage (replacing any previous active usage for this role).

        This is the PRIMARY method that domain services should call.

        Args:
            file:         Django UploadedFile.
            owner_type:   OwnerType constant (e.g. OwnerType.ORGANIZATION).
            owner_id:     UUID of the owning entity.
            role:         AssetCategory constant (e.g. AssetCategory.LOGO).
            name:         Human-readable asset name.
            tenant:       Tenant instance (for namespaced storage paths).
            uploaded_by:  User who uploaded the file.
            visibility:   AssetVisibility constant.
            images_only:  If True, only image MIME types are accepted.

        Returns:
            Created MediaAsset instance (ready status, CDN URL populated).

        Raises:
            UnsupportedMediaType: Invalid file type.
            MediaAssetTooLarge:   File too large.
            MediaAssetUploadFailed: Storage error.
        """
        # 1. Validate
        if images_only:
            mime_type, extension, asset_type = validate_image_upload(file)
        else:
            mime_type, extension, asset_type = validate_upload(file)

        # 2. Compute checksum before upload (seek to start)
        file.seek(0)
        checksum = MediaAsset.compute_checksum(file)
        file.seek(0)

        # 3. Build storage key
        file_uuid = str(uuid.uuid4())
        tenant_slug = tenant.slug if tenant else None

        object_key = MediaAssetService._build_object_key(
            owner_type=owner_type,
            owner_id=owner_id,
            role=role,
            file_uuid=file_uuid,
            extension=extension,
            tenant_slug=tenant_slug,
        )

        # 4. Upload to storage
        try:
            provider = get_storage_provider()
            cdn_url = provider.upload(
                file_obj=file,
                object_key=object_key,
                content_type=mime_type,
                public=(visibility == AssetVisibility.PUBLIC),
            )
        except Exception as exc:
            logger.exception("Storage upload failed for key: %s", object_key)
            raise MediaAssetUploadFailed(detail=str(exc)) from exc

        # 5. Create MediaAsset record
        asset = MediaAsset.objects.create(
            name=name,
            asset_type=asset_type,
            category=role,
            original_filename=getattr(file, "name", ""),
            mime_type=mime_type,
            extension=extension,
            size_bytes=file.size,
            checksum_sha256=checksum,
            bucket=getattr(settings, "CLOUDFLARE_R2_BUCKET", "local"),
            object_key=object_key,
            cdn_url=cdn_url,
            owner_type=owner_type,
            owner_id=owner_id,
            tenant=tenant,
            visibility=visibility,
            status=AssetStatus.READY,
            uploaded_by=uploaded_by,
        )

        # 6. Link to owner via MediaUsage (replacing previous)
        MediaUsage.replace_for(
            owner_type=owner_type,
            owner_id=owner_id,
            role=role,
            new_asset=asset,
        )

        logger.info(
            "Asset uploaded: %s (owner=%s/%s, role=%s)",
            asset.id, owner_type, owner_id, role,
        )

        # 7. Queue thumbnail generation (async)
        MediaAssetService._queue_thumbnail_task(asset_id=str(asset.id))

        return asset

    @staticmethod
    def _queue_thumbnail_task(*, asset_id: str) -> None:
        """
        Enqueue the Celery thumbnail generation task.
        Fails silently if Celery is not available (dev environment).
        """
        try:
            from media_assets.tasks import generate_thumbnails
            generate_thumbnails.delay(asset_id)
        except Exception:
            logger.debug(
                "Thumbnail task not queued (Celery may not be running): asset=%s",
                asset_id,
            )

    @staticmethod
    def get_asset(*, asset_id: str) -> MediaAsset:
        """
        Fetch a MediaAsset by ID.

        Raises:
            MediaAssetNotFound: If the asset does not exist.
        """
        try:
            return MediaAsset.objects.get(id=asset_id)
        except MediaAsset.DoesNotExist:
            raise MediaAssetNotFound()

    @staticmethod
    @transaction.atomic
    def delete_asset(*, asset_id: str) -> None:
        """
        Soft-delete a MediaAsset:
        1. Mark as DELETED in the database.
        2. Deactivate all related MediaUsage records.
        3. Queue async physical deletion from storage.

        The physical file is deleted asynchronously to avoid
        blocking the API response.
        """
        try:
            asset = MediaAsset.objects.get(id=asset_id)
        except MediaAsset.DoesNotExist:
            raise MediaAssetNotFound()

        # Deactivate all usages
        MediaUsage.objects.filter(asset=asset).update(is_active=False)

        # Mark as deleted
        asset.status = AssetStatus.DELETED
        asset.save(update_fields=["status", "updated_at"])

        logger.info("Asset soft-deleted: %s", asset_id)

        # Queue physical deletion
        try:
            from media_assets.tasks import delete_asset_from_storage
            delete_asset_from_storage.delay(asset_id, asset.object_key)
        except Exception:
            logger.debug("Physical deletion task not queued: asset=%s", asset_id)

    @staticmethod
    def get_usage_url(
        *,
        owner_type: str,
        owner_id,
        role: str,
        variant: str | None = None,
    ) -> str | None:
        """
        Convenience method: returns the public URL for the active asset
        linked to the given owner+role, or None if none exists.

        Args:
            owner_type: OwnerType constant.
            owner_id:   UUID of the owning entity.
            role:       AssetCategory constant.
            variant:    Optional variant type (thumbnail, small, etc.)

        Returns:
            CDN URL string, or None.
        """
        usage = MediaUsage.get_active_for(
            owner_type=owner_type,
            owner_id=owner_id,
            role=role,
        )

        if not usage:
            return None

        if variant:
            var = usage.asset.variants.filter(variant_type=variant).first()
            if var:
                return var.cdn_url

        return usage.asset.public_url
