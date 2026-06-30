"""
BOLAYETU — Organization Serializers

Serializers for organization (tenant) endpoints.
These handle INPUT validation and OUTPUT serialization.
No business logic lives here.
"""

from rest_framework import serializers

from core.models import Tenant
from organizations.constants import OrganizationType, OrganizationStatus


class OrganizationSerializer(serializers.ModelSerializer):
    """
    Full organization serializer for authenticated users.

    Used for: GET /api/v1/organizations/me/
    """

    logo_url = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    verified = serializers.SerializerMethodField()
    type_label = serializers.SerializerMethodField()
    status_label = serializers.SerializerMethodField()

    class Meta:
        model = Tenant
        fields = [
            "id",
            "name",
            "slug",
            "type",
            "type_label",
            "logo",
            "logo_url",
            "banner",
            "banner_url",
            "primary_color",
            "secondary_color",
            "country",
            "city",
            "location",
            "email",
            "phone",
            "website",
            "description",
            "is_public",
            "is_verified",
            "verified",
            "status",
            "status_label",
            "subdomain",
            "language",
            "timezone",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id", "slug", "logo_url", "banner_url", "location", "verified",
            "type_label", "status_label", "created_at", "updated_at",
        ]

    def get_logo_url(self, obj: Tenant) -> str:
        """Return the full logo URL or empty string."""
        try:
            # If ImageField/FieldFile is used, .url provides the public URL
            if getattr(obj, "logo"):
                return obj.logo.url
        except Exception:
            pass
        # Fallback to attribute (string) or empty
        return getattr(obj, "logo", "") or ""

    def get_banner_url(self, obj: Tenant) -> str:
        """Return the full banner URL or empty string."""
        try:
            if getattr(obj, "banner"):
                return obj.banner.url
        except Exception:
            pass
        return getattr(obj, "banner", "") or ""

    def get_location(self, obj: Tenant) -> str:
        """Return a combined location string."""
        parts = [p for p in [obj.city, obj.country] if p]
        return ", ".join(parts)

    def get_verified(self, obj: Tenant) -> bool:
        """Return verification status."""
        return obj.is_verified

    def get_type_label(self, obj: Tenant) -> str:
        """Return the human-readable type label."""
        return OrganizationType.LABELS.get(obj.type, obj.type)

    def get_status_label(self, obj: Tenant) -> str:
        """Return the human-readable status label."""
        labels = dict(OrganizationStatus.CHOICES)
        return labels.get(obj.status, obj.status)


class OrganizationUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating an organization via PATCH /api/v1/organizations/me/.

    Only the fields below are updatable. Subdomain, slug, status,
    and verification are managed through separate admin endpoints.
    """

    class Meta:
        model = Tenant
        fields = [
            "name",
            "type",
            "primary_color",
            "secondary_color",
            "country",
            "city",
            "email",
            "phone",
            "website",
            "description",
            "is_public",
            "language",
            "timezone",
        ]


class PublicOrganizationSerializer(serializers.ModelSerializer):
    """
    Serializer for public organization listing.

    Used for: GET /api/v1/organizations/public/
    """

    logo_url = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    verified = serializers.SerializerMethodField()
    type_label = serializers.SerializerMethodField()
    active_subscribers = serializers.SerializerMethodField()

    class Meta:
        model = Tenant
        fields = [
            "id",
            "name",
            "slug",
            "type",
            "type_label",
            "logo",
            "logo_url",
            "primary_color",
            "secondary_color",
            "country",
            "city",
            "location",
            "email",
            "phone",
            "website",
            "description",
            "is_public",
            "is_verified",
            "verified",
            "active_subscribers",
            "created_at",
        ]
        read_only_fields = fields

    def get_logo_url(self, obj: Tenant) -> str:
        try:
            if getattr(obj, "logo"):
                return obj.logo.url
        except Exception:
            pass
        return getattr(obj, "logo", "") or ""

    def get_banner_url(self, obj: Tenant) -> str:
        try:
            if getattr(obj, "banner"):
                return obj.banner.url
        except Exception:
            pass
        return getattr(obj, "banner", "") or ""

    def get_location(self, obj: Tenant) -> str:
        parts = [p for p in [obj.city, obj.country] if p]
        return ", ".join(parts)

    def get_verified(self, obj: Tenant) -> bool:
        return obj.is_verified

    def get_type_label(self, obj: Tenant) -> str:
        return OrganizationType.LABELS.get(obj.type, obj.type)

    def get_active_subscribers(self, obj: Tenant) -> int:
        """Return the count of active subscribers."""
        if hasattr(obj, "_subscriber_count"):
            return obj._subscriber_count
        return obj.subscriptions.filter(is_active=True).count()


class OrganizationKpisSerializer(serializers.Serializer):
    """
    Serializer for organization KPI statistics.

    Used for: GET /api/v1/organizations/public/:slug/kpis/
    """

    total_games = serializers.IntegerField()
    total_goals = serializers.IntegerField()
    goals_per_game = serializers.FloatField()
    live_games = serializers.IntegerField()
    scheduled_games = serializers.IntegerField()
    active_subscribers = serializers.IntegerField()
    total_tournaments = serializers.IntegerField()
    active_tournaments = serializers.IntegerField()
    upcoming_tournaments = serializers.IntegerField()
    completed_tournaments = serializers.IntegerField()
    total_clubs = serializers.IntegerField()


class OrganizationHistoryEntrySerializer(serializers.Serializer):
    """
    Serializer for organization tournament history entries.

    Used for: GET /api/v1/organizations/public/:slug/history/
    """

    season = serializers.CharField()
    tournament_name = serializers.CharField()
    tournament_id = serializers.CharField()
    tournament_format = serializers.CharField()
    winner_club_name = serializers.CharField()
    runner_up_club_name = serializers.CharField()
    winner_club_id = serializers.CharField()
    runner_up_club_id = serializers.CharField()


class SubscriptionResponseSerializer(serializers.Serializer):
    """
    Serializer for subscribe/unsubscribe response.
    """

    subscribed = serializers.BooleanField()
    organization_id = serializers.UUIDField()


class OnboardingStatusSerializer(serializers.Serializer):
    """Onboarding gate status for the authenticated user's organization."""

    onboarding_required = serializers.BooleanField()
    has_organization = serializers.BooleanField()
    is_organization_admin = serializers.BooleanField()
    competitions_count = serializers.IntegerField()
    organization = OrganizationSerializer(allow_null=True)
