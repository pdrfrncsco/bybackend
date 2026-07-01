"""
BOLAYETU — MediaVariant Model

Represents a processed/resized variant of a MediaAsset.

Architecture (08A_DIGITAL_ASSET_MANAGEMENT.md §12):
    After upload, Celery tasks generate variants:
        - thumbnail  (150×150)
        - small      (320×240)
        - medium     (640×480)
        - large      (1280×960)
        - webp       (converted format)
        - avif       (converted format)

    Each variant is stored as a separate object in R2 and linked
    back to the original MediaAsset.
"""

from django.db import models

from common.models import BaseModel
from media_assets.constants import AssetVariantType


class MediaVariant(BaseModel):
    """
    A processed version (thumbnail, resized, format-converted) of a MediaAsset.

    Variants are generated asynchronously by Celery after the original
    file is uploaded. The frontend should always prefer an appropriate
    variant over the original for performance.
    """

    asset = models.ForeignKey(
        "media_assets.MediaAsset",
        on_delete=models.CASCADE,
        related_name="variants",
        verbose_name="Asset",
    )
    variant_type = models.CharField(
        max_length=20,
        choices=AssetVariantType.choices,
        verbose_name="Variant Type",
    )
    object_key = models.CharField(
        max_length=1000,
        verbose_name="Object Key",
        help_text="Storage path/key for this variant.",
    )
    cdn_url = models.URLField(
        max_length=2000,
        blank=True,
        verbose_name="CDN URL",
    )
    width = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Width (px)",
    )
    height = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Height (px)",
    )
    size_bytes = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name="Size (bytes)",
    )
    mime_type = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="MIME Type",
    )

    class Meta:
        ordering = ["variant_type"]
        verbose_name = "Media Variant"
        verbose_name_plural = "Media Variants"
        constraints = [
            models.UniqueConstraint(
                fields=["asset", "variant_type"],
                name="unique_variant_per_asset",
            )
        ]
        indexes = [
            models.Index(fields=["asset", "variant_type"]),
        ]

    def __str__(self) -> str:
        return f"{self.asset.name} — {self.variant_type}"
