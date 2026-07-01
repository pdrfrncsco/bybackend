"""
BOLAYETU — MediaAsset Model

Represents any digital file (image, document, video, audio) managed
by the Bolayetu platform.

Architecture (08A_DIGITAL_ASSET_MANAGEMENT.md):
    - MediaAsset is a GLOBAL entity — it never belongs exclusively to one module.
    - Physical files are stored in Cloudflare R2 (or local dev storage).
    - Only metadata is stored in the database.
    - Every module must reference files through MediaAsset + MediaUsage.
    - Rule: NEVER store file paths directly in domain models.

Owner types:
    - organization  → Tenant
    - club          → Club
    - competition   → Competition
    - player        → Player (future)
    - match         → Match (future)
    - news          → News (future)
    - system        → Internal platform assets
"""

import hashlib
import os
import uuid

from django.conf import settings
from django.db import models
from django.utils.text import slugify

from common.models import BaseModel
from media_assets.constants import (
    AssetType,
    AssetCategory,
    AssetVisibility,
    AssetStatus,
    OwnerType,
)


class MediaAsset(BaseModel):
    """
    Represents a digital asset (file) managed by the Bolayetu platform.

    The file is stored in Cloudflare R2 (production) or the local
    filesystem (development). Only metadata is persisted in PostgreSQL.

    One MediaAsset can be used by many objects via MediaUsage records.
    This avoids file duplication across the platform.
    """

    # ─── Identity ────────────────────────────────────────────────────────
    name = models.CharField(
        max_length=255,
        verbose_name="Name",
        help_text="Human-readable name for this asset (e.g. 'FAF Logo 2025').",
    )
    slug = models.SlugField(
        max_length=255,
        blank=True,
        verbose_name="Slug",
    )

    # ─── Classification ──────────────────────────────────────────────────
    asset_type = models.CharField(
        max_length=20,
        choices=AssetType.choices,
        default=AssetType.IMAGE,
        verbose_name="Type",
    )
    category = models.CharField(
        max_length=30,
        choices=AssetCategory.choices,
        default=AssetCategory.LOGO,
        verbose_name="Category",
    )

    # ─── File Metadata ───────────────────────────────────────────────────
    original_filename = models.CharField(
        max_length=500,
        verbose_name="Original Filename",
        help_text="The name of the file as provided by the user.",
    )
    mime_type = models.CharField(
        max_length=100,
        verbose_name="MIME Type",
        help_text="e.g. image/jpeg, image/png, application/pdf",
    )
    extension = models.CharField(
        max_length=20,
        verbose_name="Extension",
        help_text="File extension without dot (e.g. 'jpg', 'png', 'pdf').",
    )
    size_bytes = models.BigIntegerField(
        verbose_name="Size (bytes)",
        help_text="File size in bytes.",
    )
    checksum_sha256 = models.CharField(
        max_length=64,
        blank=True,
        verbose_name="SHA-256 Checksum",
        help_text="SHA-256 hash of the file content for integrity verification.",
    )

    # ─── Image Metadata (populated async by Celery) ──────────────────────
    width = models.PositiveIntegerField(null=True, blank=True, verbose_name="Width (px)")
    height = models.PositiveIntegerField(null=True, blank=True, verbose_name="Height (px)")

    # ─── Storage ─────────────────────────────────────────────────────────
    bucket = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Bucket",
        help_text="Storage bucket name (e.g. bolayetu-storage).",
    )
    object_key = models.CharField(
        max_length=1000,
        verbose_name="Object Key",
        help_text="The path/key within the bucket (e.g. tenant/faf/logos/uuid.jpg).",
    )
    cdn_url = models.URLField(
        max_length=2000,
        blank=True,
        verbose_name="CDN URL",
        help_text="Public CDN URL for this asset (Cloudflare CDN or local).",
    )
    private_url = models.URLField(
        max_length=2000,
        blank=True,
        verbose_name="Private URL",
        help_text="Direct storage URL (use for internal operations only).",
    )
    thumbnail_url = models.URLField(
        max_length=2000,
        blank=True,
        verbose_name="Thumbnail URL",
        help_text="URL of the generated thumbnail variant.",
    )

    # ─── Ownership ───────────────────────────────────────────────────────
    owner_type = models.CharField(
        max_length=20,
        choices=OwnerType.choices,
        default=OwnerType.ORGANIZATION,
        verbose_name="Owner Type",
    )
    owner_id = models.UUIDField(
        null=True,
        blank=True,
        verbose_name="Owner ID",
        help_text="UUID of the owning entity (Tenant, Club, etc.).",
    )

    # ─── Multi-Tenant ────────────────────────────────────────────────────
    tenant = models.ForeignKey(
        "core.Tenant",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="media_assets",
        verbose_name="Tenant",
        help_text="Tenant that owns this asset. Null for system assets.",
    )

    # ─── Access Control ──────────────────────────────────────────────────
    visibility = models.CharField(
        max_length=20,
        choices=AssetVisibility.choices,
        default=AssetVisibility.PUBLIC,
        verbose_name="Visibility",
    )

    # ─── Status ──────────────────────────────────────────────────────────
    status = models.CharField(
        max_length=20,
        choices=AssetStatus.choices,
        default=AssetStatus.READY,
        verbose_name="Status",
    )

    # ─── Audit ───────────────────────────────────────────────────────────
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_assets",
        verbose_name="Uploaded By",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Media Asset"
        verbose_name_plural = "Media Assets"
        indexes = [
            models.Index(fields=["tenant", "owner_type", "owner_id"]),
            models.Index(fields=["asset_type", "category"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.asset_type})"

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.name) or str(self.id)
        super().save(*args, **kwargs)

    @property
    def is_ready(self) -> bool:
        """Returns True if the asset is ready for use."""
        from media_assets.constants import AssetStatus as _AS
        return self.status == _AS.READY

    @property
    def public_url(self) -> str:
        """Returns the best available public URL for this asset."""
        return self.cdn_url or self.private_url or ""

    @classmethod
    def compute_checksum(cls, file_obj) -> str:
        """Compute SHA-256 checksum of a file-like object."""
        sha256 = hashlib.sha256()
        for chunk in file_obj.chunks():
            sha256.update(chunk)
        return sha256.hexdigest()
