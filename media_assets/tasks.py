"""
BOLAYETU — Media Asset Celery Tasks

Asynchronous tasks for:
    1. Generating image thumbnails/variants after upload.
    2. Physically deleting files from storage after soft-delete.

Architecture (08_MEDIA_STORAGE_ARCHITECTURE.md §18):
    After upload, Celery generates:
        - thumbnail  (150×150)
        - small      (320×240)
        - medium     (640×480)
        - large      (1280×960)

    Uses Pillow for image processing.
    Falls back gracefully if Pillow is not available.
"""

import io
import logging
import uuid

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    name="media_assets.generate_thumbnails",
)
def generate_thumbnails(self, asset_id: str) -> dict:
    """
    Generate resized variants for an image MediaAsset.

    Queued automatically after every upload.
    Silently skips non-image assets.

    Args:
        asset_id: UUID string of the MediaAsset.

    Returns:
        Dict with variant urls or skip reason.
    """
    from media_assets.constants import AssetStatus, AssetType, AssetVariantType, THUMBNAIL_SIZES
    from media_assets.models import MediaAsset, MediaVariant
    from media_assets.storage import get_storage_provider

    try:
        asset = MediaAsset.objects.get(id=asset_id)
    except MediaAsset.DoesNotExist:
        logger.error("generate_thumbnails: asset not found: %s", asset_id)
        return {"error": "asset_not_found"}

    # Only process images
    if asset.asset_type not in (AssetType.IMAGE,):
        logger.debug("generate_thumbnails: skipping non-image asset %s", asset_id)
        return {"skipped": "not_an_image"}

    # Require Pillow
    try:
        from PIL import Image
    except ImportError:
        logger.warning(
            "generate_thumbnails: Pillow not installed, skipping thumbnail generation."
        )
        return {"skipped": "pillow_not_installed"}

    # Fetch the original file from storage
    try:
        provider = get_storage_provider()
    except Exception as exc:
        logger.exception("generate_thumbnails: failed to get storage provider")
        raise self.retry(exc=exc)

    # Download original — local storage reads directly from filesystem
    original_data = _read_original(provider, asset)

    if not original_data:
        logger.error("generate_thumbnails: could not read original file for %s", asset_id)
        return {"error": "original_not_readable"}

    try:
        img = Image.open(io.BytesIO(original_data))
        # Update image dimensions on asset
        if not asset.width or not asset.height:
            asset.width = img.width
            asset.height = img.height
            asset.save(update_fields=["width", "height"])
    except Exception as exc:
        logger.exception("generate_thumbnails: failed to open image %s", asset_id)
        raise self.retry(exc=exc)

    generated = {}

    for variant_type, (max_w, max_h) in THUMBNAIL_SIZES.items():
        try:
            # Skip if variant already exists
            if MediaVariant.objects.filter(asset=asset, variant_type=variant_type).exists():
                continue

            # Resize preserving aspect ratio
            resized = img.copy()
            resized.thumbnail((max_w, max_h), Image.LANCZOS)

            # Convert to RGB if needed (e.g. RGBA PNG)
            if resized.mode in ("RGBA", "P"):
                resized = resized.convert("RGB")

            buffer = io.BytesIO()
            resized.save(buffer, format="JPEG", quality=85, optimize=True)
            buffer.seek(0)

            # Build variant object key
            variant_uuid = str(uuid.uuid4())
            ext = "jpg"
            tenant_slug = asset.tenant.slug if asset.tenant else None
            base_dir = f"tenant/{tenant_slug}" if tenant_slug else "system"
            variant_key = (
                f"{base_dir}/{asset.owner_type}/{asset.category}/"
                f"variants/{variant_type}/{variant_uuid}.{ext}"
            )

            cdn_url = provider.upload(
                file_obj=buffer,
                object_key=variant_key,
                content_type="image/jpeg",
                public=True,
            )

            MediaVariant.objects.create(
                asset=asset,
                variant_type=variant_type,
                object_key=variant_key,
                cdn_url=cdn_url,
                width=resized.width,
                height=resized.height,
                size_bytes=buffer.tell(),
                mime_type="image/jpeg",
            )

            generated[variant_type] = cdn_url
            logger.info(
                "Variant generated: asset=%s variant=%s url=%s",
                asset_id, variant_type, cdn_url,
            )

        except Exception as exc:
            logger.exception(
                "generate_thumbnails: failed variant %s for asset %s",
                variant_type, asset_id,
            )
            # Continue with other variants even if one fails

    # Update thumbnail_url on the asset itself
    thumb = generated.get(AssetVariantType.THUMBNAIL)
    if thumb and not asset.thumbnail_url:
        asset.thumbnail_url = thumb
        asset.save(update_fields=["thumbnail_url"])

    return {"generated": generated}


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="media_assets.delete_asset_from_storage",
)
def delete_asset_from_storage(self, asset_id: str, object_key: str) -> dict:
    """
    Physically delete a file from storage after soft-delete.

    Args:
        asset_id:   UUID string of the MediaAsset (for logging).
        object_key: Storage key to delete.
    """
    from media_assets.models import MediaAsset, MediaVariant
    from media_assets.storage import get_storage_provider

    try:
        provider = get_storage_provider()
        provider.delete(object_key=object_key)
        logger.info("Physical delete: %s (asset=%s)", object_key, asset_id)

        # Delete variant files too
        try:
            asset = MediaAsset.objects.get(id=asset_id)
            for variant in asset.variants.all():
                try:
                    provider.delete(object_key=variant.object_key)
                    variant.delete()
                except Exception:
                    logger.warning("Failed to delete variant: %s", variant.object_key)
        except MediaAsset.DoesNotExist:
            pass

        return {"deleted": object_key}

    except Exception as exc:
        logger.exception("Failed to delete from storage: %s", object_key)
        raise self.retry(exc=exc)


def _read_original(provider, asset) -> bytes | None:
    """Read original file bytes from storage."""
    from media_assets.storage.local import LocalStorageProvider

    if isinstance(provider, LocalStorageProvider):
        from django.core.files.storage import default_storage
        try:
            with default_storage.open(asset.object_key, "rb") as f:
                return f.read()
        except Exception:
            return None

    # R2: download via presigned URL or boto3 get_object
    try:
        client = provider._get_client()
        response = client.get_object(Bucket=provider.bucket, Key=asset.object_key)
        return response["Body"].read()
    except Exception:
        return None
