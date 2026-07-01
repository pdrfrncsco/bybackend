"""
BOLAYETU — Media Asset Selectors

Read-only queries for the DAM module.
Selectors are the single source of truth for fetching media data.

Architecture (02_BACKEND_GUIDE.md):
    - Selectors handle all DB reads for a module.
    - Views/serializers must never write raw ORM queries — use selectors.
    - Selectors return querysets or model instances, never serialized data.
"""

from django.db.models import QuerySet

from media_assets.models import MediaAsset, MediaUsage, MediaVariant


class MediaAssetSelector:
    """Read-only queries for MediaAsset."""

    @staticmethod
    def get_by_id(*, asset_id: str) -> MediaAsset | None:
        """Return a MediaAsset by ID, or None if not found."""
        return MediaAsset.objects.filter(id=asset_id).first()

    @staticmethod
    def get_by_tenant(*, tenant_id) -> QuerySet:
        """Return all non-deleted assets for a tenant."""
        from media_assets.constants import AssetStatus
        return (
            MediaAsset.objects
            .filter(tenant_id=tenant_id)
            .exclude(status=AssetStatus.DELETED)
            .order_by("-created_at")
        )

    @staticmethod
    def get_by_owner(*, owner_type: str, owner_id) -> QuerySet:
        """Return all active assets for a specific owner."""
        from media_assets.constants import AssetStatus
        return (
            MediaAsset.objects
            .filter(owner_type=owner_type, owner_id=owner_id)
            .exclude(status=AssetStatus.DELETED)
            .order_by("-created_at")
        )

    @staticmethod
    def search(
        *,
        tenant_id=None,
        asset_type: str | None = None,
        category: str | None = None,
        query: str | None = None,
    ) -> QuerySet:
        """
        Search assets with optional filters.

        Args:
            tenant_id:  Filter by tenant.
            asset_type: Filter by AssetType.
            category:   Filter by AssetCategory.
            query:      Search in name field.
        """
        from media_assets.constants import AssetStatus

        qs = MediaAsset.objects.exclude(status=AssetStatus.DELETED)

        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        if asset_type:
            qs = qs.filter(asset_type=asset_type)
        if category:
            qs = qs.filter(category=category)
        if query:
            qs = qs.filter(name__icontains=query)

        return qs.order_by("-created_at")


class MediaUsageSelector:
    """Read-only queries for MediaUsage."""

    @staticmethod
    def get_active(*, owner_type: str, owner_id, role: str) -> MediaUsage | None:
        """Return the current active usage for a given owner + role."""
        return (
            MediaUsage.objects
            .filter(owner_type=owner_type, owner_id=owner_id, role=role, is_active=True)
            .select_related("asset")
            .first()
        )

    @staticmethod
    def get_all_for_owner(*, owner_type: str, owner_id) -> QuerySet:
        """Return all active usages for an owner."""
        return (
            MediaUsage.objects
            .filter(owner_type=owner_type, owner_id=owner_id, is_active=True)
            .select_related("asset")
            .order_by("role", "order")
        )

    @staticmethod
    def get_url(
        *,
        owner_type: str,
        owner_id,
        role: str,
        variant: str | None = None,
    ) -> str | None:
        """
        Convenience method: return the CDN URL for an active usage.

        Returns None if no active usage exists.
        """
        usage = MediaUsageSelector.get_active(
            owner_type=owner_type,
            owner_id=owner_id,
            role=role,
        )

        if not usage:
            return None

        if variant:
            var = usage.asset.variants.filter(variant_type=variant).first()
            if var and var.cdn_url:
                return var.cdn_url

        return usage.asset.public_url or None


class MediaVariantSelector:
    """Read-only queries for MediaVariant."""

    @staticmethod
    def get_variants(*, asset_id) -> QuerySet:
        """Return all variants for an asset."""
        return MediaVariant.objects.filter(asset_id=asset_id).order_by("variant_type")

    @staticmethod
    def get_variant(*, asset_id, variant_type: str) -> MediaVariant | None:
        """Return a specific variant for an asset."""
        return MediaVariant.objects.filter(
            asset_id=asset_id, variant_type=variant_type
        ).first()
