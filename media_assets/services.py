"""
BOLAYETU — Media Asset Service

Centralized service for uploading, managing, and retrieving digital assets.
All file operations go through this service to ensure R2 storage, deduplication,
and proper metadata tracking.
"""

import hashlib
import os
from typing import Optional
from django.core.files.uploadedfile import UploadedFile
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.conf import settings

from media_assets.models import MediaAsset, MediaUsage, MediaVariant
from media_assets.constants import (
    AssetType,
    AssetCategory,
    AssetVisibility,
    OwnerType,
)


class MediaAssetService:
    """
    Central service for all digital asset operations.
    
    All file uploads, deletion, and asset management must go through this service.
    
    This ensures:
        - Consistent storage in Cloudflare R2 (configured via DEFAULT_FILE_STORAGE)
        - Deduplication via SHA256 checksums
        - Proper metadata tracking
        - Usage linking across modules
    """

    @staticmethod
    def compute_checksum(file_content: bytes) -> str:
        """Compute SHA256 checksum of file content."""
        return hashlib.sha256(file_content).hexdigest()

    @staticmethod
    def upload_file(
        file: UploadedFile,
        name: str,
        category: str = AssetCategory.LOGO,
        visibility: str = AssetVisibility.PUBLIC,
        tenant=None,
        uploaded_by=None,
        owner_type: str = OwnerType.ORGANIZATION,
        owner_id=None,
    ) -> MediaAsset:
        """
        Upload a file and create a MediaAsset record.
        
        If a file with the same checksum already exists, reuse it (deduplication).
        
        Args:
            file: Django UploadedFile object
            name: Human-readable name for the asset
            category: AssetCategory choice (logo, banner, avatar, etc.)
            visibility: AssetVisibility choice (public, internal, private)
            tenant: Optional tenant reference
            uploaded_by: User who uploaded (optional)
            owner_type: Type of owner (organization, club, player, etc.)
            owner_id: ID of the owning entity
        
        Returns:
            MediaAsset instance
        """
        from django.utils.text import slugify
        
        # Read file content for checksum
        file_content = file.read()
        file.seek(0)  # Reset for storage
        
        checksum = MediaAssetService.compute_checksum(file_content)
        
        # Check for duplicate
        existing = MediaAsset.objects.filter(checksum_sha256=checksum).first()
        if existing:
            return existing
        
        # Extract file metadata
        original_filename = file.name
        extension = os.path.splitext(original_filename)[1].lstrip('.').lower()
        mime_type = file.content_type or 'application/octet-stream'
        
        # Determine asset type
        if mime_type.startswith('image/'):
            asset_type = AssetType.IMAGE
        elif mime_type.startswith('video/'):
            asset_type = AssetType.VIDEO
        elif mime_type.startswith('audio/'):
            asset_type = AssetType.AUDIO
        elif 'pdf' in mime_type:
            asset_type = AssetType.PDF
        elif 'document' in mime_type or 'word' in mime_type:
            asset_type = AssetType.DOCUMENT
        else:
            asset_type = AssetType.IMAGE
        
        # Generate storage path
        if tenant:
            storage_path = f"tenants/{tenant.id}/{category}/{checksum[:8]}-{slugify(name)}.{extension}"
        else:
            storage_path = f"assets/{category}/{checksum[:8]}-{slugify(name)}.{extension}"
        
        # Save to storage (via DEFAULT_FILE_STORAGE)
        from django.core.files.storage import default_storage
        saved_path = default_storage.save(storage_path, file)
        
        # Get CDN URL
        cdn_url = default_storage.url(saved_path)
        
        # Create MediaAsset record
        asset = MediaAsset.objects.create(
            name=name,
            slug=slugify(name),
            asset_type=asset_type,
            category=category,
            mime_type=mime_type,
            extension=extension,
            original_filename=original_filename,
            size_bytes=file.size,
            checksum_sha256=checksum,
            object_key=saved_path,
            cdn_url=cdn_url,
            visibility=visibility,
            tenant=tenant,
            uploaded_by=uploaded_by,
            owner_type=owner_type,
            owner_id=owner_id,
        )
        
        return asset

    @staticmethod
    def upload_for_owner(
        file: UploadedFile,
        owner_type: str,
        owner_id,
        role: str,  # AssetCategory
        name: str,
        tenant=None,
        uploaded_by=None,
        images_only: bool = False,
    ) -> MediaAsset:
        """
        Upload a file for a specific owner (Organization, Club, Player, etc.).
        
        Args:
            file: Uploaded file
            owner_type: Type of owner (from OwnerType choices)
            owner_id: ID of the owner
            role: Usage category (from AssetCategory)
            name: Human-readable name
            tenant: Optional tenant association
            uploaded_by: User who uploaded
            images_only: If True, validate that file is an image
        
        Returns:
            MediaAsset instance
        
        Raises:
            UnsupportedMediaType: If file type is not supported
            MediaAssetTooLarge: If file exceeds size limit
        """
        from media_assets.exceptions import (
            UnsupportedMediaType,
            MediaAssetTooLarge,
            InvalidMediaFile,
        )
        
        # Validate file size (10 MB limit)
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
        if file.size > MAX_FILE_SIZE:
            raise MediaAssetTooLarge(
                detail=f"File size exceeds 10 MB limit ({file.size / 1024 / 1024:.1f} MB)"
            )
        
        # Validate file type
        mime_type = file.content_type or 'application/octet-stream'
        if images_only and not mime_type.startswith('image/'):
            raise UnsupportedMediaType(
                detail=f"Only image files are supported. Got {mime_type}"
            )
        
        # Upload
        return MediaAssetService.upload_file(
            file=file,
            name=name,
            category=role,
            visibility=AssetVisibility.PUBLIC,
            tenant=tenant,
            uploaded_by=uploaded_by,
            owner_type=owner_type,
            owner_id=owner_id,
        )

    @staticmethod
    def link_asset_to_object(
        asset: MediaAsset,
        obj,
        usage_type: str = MediaUsage.UsageType.LOGO,
        is_primary: bool = True,
    ) -> MediaUsage:
        """
        Link a MediaAsset to an object (Organization, Club, Player, etc.).
        
        Args:
            asset: MediaAsset instance
            obj: The object to link to (any Django model instance with an id/pk)
            usage_type: Type of usage (logo, banner, avatar, etc.)
            is_primary: Whether this is the primary/default usage
        
        Returns:
            MediaUsage instance
        """
        content_type = ContentType.objects.get_for_model(type(obj))
        
        # If this is primary, deactivate other primary usages for this object
        if is_primary:
            MediaUsage.objects.filter(
                content_type=content_type,
                object_id=obj.pk,
                usage_type=usage_type,
                is_primary=True,
            ).update(is_primary=False)
        
        # Create or update usage
        usage, created = MediaUsage.objects.get_or_create(
            asset=asset,
            content_type=content_type,
            object_id=obj.pk,
            usage_type=usage_type,
            defaults={'is_primary': is_primary},
        )
        
        if not created and usage.is_primary != is_primary:
            usage.is_primary = is_primary
            usage.save(update_fields=['is_primary'])
        
        return usage

    @staticmethod
    def get_asset_for_object(
        obj,
        usage_type: str = MediaUsage.UsageType.LOGO,
    ) -> Optional[MediaAsset]:
        """
        Get the primary asset linked to an object.
        
        Args:
            obj: The object to get asset for
            usage_type: Type of usage (logo, banner, etc.)
        
        Returns:
            MediaAsset or None
        """
        content_type = ContentType.objects.get_for_model(type(obj))
        
        usage = MediaUsage.objects.filter(
            content_type=content_type,
            object_id=obj.pk,
            usage_type=usage_type,
            is_primary=True,
        ).select_related('asset').first()
        
        return usage.asset if usage else None

    @staticmethod
    def delete_asset(asset: MediaAsset) -> bool:
        """
        Delete an asset and its file from storage.
        
        Args:
            asset: MediaAsset to delete
        
        Returns:
            True if successful
        """
        try:
            from django.core.files.storage import default_storage
            
            # Delete from storage
            if asset.object_key:
                default_storage.delete(asset.object_key)
            
            # Delete variants
            for variant in asset.variants.all():
                if variant.object_key or hasattr(variant, 'object_key'):
                    try:
                        default_storage.delete(variant.object_key)
                    except:
                        pass
            
            # Delete from database (cascade will delete usages and variants)
            asset.delete()
            return True
        except Exception as e:
            return False
