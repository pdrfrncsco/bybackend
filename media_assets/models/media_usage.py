"""
BOLAYETU — MediaUsage Model

Links a MediaAsset to any domain entity without duplicating the file.

Architecture (08A_DIGITAL_ASSET_MANAGEMENT.md §14):
    Instead of storing file paths directly in Organization, Club, Player, etc.,
    we create a MediaUsage record that links the entity to the MediaAsset.

    Example:
        Tenant "FAF" uses MediaAsset "faf-logo.png" as their logo.
        → MediaUsage(asset=faf_logo, owner_type="organization", owner_id=faf_tenant_id, role="logo")

    The same asset can be referenced multiple times (e.g., a logo used
    in the organization profile AND a news article).

    Rule: ALWAYS use MediaUsage for relationships — never store asset IDs
    directly in domain model fields.
"""

from django.db import models

from common.models import BaseModel
from media_assets.constants import AssetCategory, OwnerType


class MediaUsage(BaseModel):
    """
    Links a MediaAsset to a domain entity.

    The combination (owner_type + owner_id + role) uniquely identifies
    a given asset slot for an entity (e.g., "the logo of club X").

    This allows:
    - Finding the current logo of any entity: filter(owner_type=..., owner_id=..., role="logo")
    - Finding all usages of an asset: asset.usages.all()
    - Replacing logos without deleting the original file
    """

    asset = models.ForeignKey(
        "media_assets.MediaAsset",
        on_delete=models.CASCADE,
        related_name="usages",
        verbose_name="Asset",
    )

    # Generic relation — identifies the owning entity
    owner_type = models.CharField(
        max_length=20,
        choices=OwnerType.choices,
        verbose_name="Owner Type",
        db_index=True,
    )
    owner_id = models.UUIDField(
        verbose_name="Owner ID",
        db_index=True,
        help_text="UUID of the owning entity (Tenant, Club, etc.).",
    )

    # Role/context of this usage (logo, banner, cover, avatar, etc.)
    role = models.CharField(
        max_length=30,
        choices=AssetCategory.choices,
        verbose_name="Role",
        help_text="How is this asset used by the owner? (logo, banner, cover, etc.)",
    )

    # Ordering for gallery-type usages
    order = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Order",
        help_text="Sort order for gallery-type usages.",
    )

    # Whether this is the currently active/primary usage
    is_active = models.BooleanField(
        default=True,
        verbose_name="Is Active",
    )

    class Meta:
        ordering = ["owner_type", "owner_id", "role", "order"]
        verbose_name = "Media Usage"
        verbose_name_plural = "Media Usages"
        indexes = [
            models.Index(fields=["owner_type", "owner_id", "role", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.owner_type}/{self.owner_id} — {self.role} — {self.asset.name}"

    @classmethod
    def get_active_for(
        cls,
        *,
        owner_type: str,
        owner_id,
        role: str,
    ) -> "MediaUsage | None":
        """
        Get the currently active asset usage for a given owner + role.

        Returns None if no active usage exists.
        """
        return (
            cls.objects
            .filter(owner_type=owner_type, owner_id=owner_id, role=role, is_active=True)
            .select_related("asset")
            .first()
        )

    @classmethod
    def replace_for(
        cls,
        *,
        owner_type: str,
        owner_id,
        role: str,
        new_asset: "media_assets.MediaAsset",  # noqa: F821
    ) -> "MediaUsage":
        """
        Replace all existing active usages for this owner+role
        with a new asset, deactivating the previous ones.

        Returns the newly created MediaUsage.
        """
        cls.objects.filter(
            owner_type=owner_type,
            owner_id=owner_id,
            role=role,
            is_active=True,
        ).update(is_active=False)

        return cls.objects.create(
            asset=new_asset,
            owner_type=owner_type,
            owner_id=owner_id,
            role=role,
            is_active=True,
        )
