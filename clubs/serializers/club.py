"""
BOLAYETU — Club Serializers

Serializers for club endpoints.
These handle INPUT validation and OUTPUT serialization.
No business logic lives here.
"""

from rest_framework import serializers

from clubs.models import Club, ClubMember
from clubs.constants import ClubStatus, ClubMemberRole


class ClubSerializer(serializers.ModelSerializer):
    """
    Full club serializer for authenticated users (club admin/management).
    """

    logo_url = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    status_label = serializers.SerializerMethodField()
    tenant_name = serializers.SerializerMethodField()
    tenant_slug = serializers.SerializerMethodField()

    class Meta:
        model = Club
        fields = [
            "id",
            "name",
            "slug",
            "short_name",
            "tenant",
            "tenant_name",
            "tenant_slug",
            "logo",
            "logo_url",
            "primary_color",
            "secondary_color",
            "founded_year",
            "stadium_name",
            "stadium_capacity",
            "country",
            "city",
            "location",
            "email",
            "phone",
            "website",
            "description",
            "is_public",
            "is_verified",
            "status",
            "status_label",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id", "slug", "logo_url", "location", "status_label",
            "tenant_name", "tenant_slug", "created_at", "updated_at",
        ]

    def get_logo_url(self, obj: Club) -> str:
        """Return the DAM logo URL if available, otherwise fall back to legacy field."""
        try:
            from media_assets.services import MediaAssetService
            from media_assets.constants import OwnerType, AssetCategory

            url = MediaAssetService.get_usage_url(
                owner_type=OwnerType.CLUB,
                owner_id=obj.id,
                role=AssetCategory.LOGO,
            )
            if url:
                return url
        except Exception:
            pass

        try:
            if getattr(obj, "logo"):
                return obj.logo.url
        except Exception:
            pass
        return getattr(obj, "logo", "") or ""

    def get_location(self, obj: Club) -> str:
        return obj.location

    def get_status_label(self, obj: Club) -> str:
        return ClubStatus.LABELS.get(obj.status, obj.status)

    def get_tenant_name(self, obj: Club) -> str:
        return obj.tenant.name if obj.tenant else ""

    def get_tenant_slug(self, obj: Club) -> str:
        return obj.tenant.slug if obj.tenant else ""


class ClubCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new club.
    """

    class Meta:
        model = Club
        fields = [
            "name",
            "short_name",
            "founded_year",
            "stadium_name",
            "stadium_capacity",
            "country",
            "city",
            "email",
            "phone",
            "website",
            "description",
            "primary_color",
            "secondary_color",
            "is_public",
        ]


class ClubUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating a club via PATCH.
    """

    class Meta:
        model = Club
        fields = [
            "name",
            "short_name",
            "founded_year",
            "stadium_name",
            "stadium_capacity",
            "country",
            "city",
            "email",
            "phone",
            "website",
            "description",
            "primary_color",
            "secondary_color",
            "is_public",
        ]


class PublicClubSerializer(serializers.ModelSerializer):
    """
    Serializer for public club listing and detail.
    """

    logo_url = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    status_label = serializers.SerializerMethodField()
    tenant_name = serializers.SerializerMethodField()
    tenant_slug = serializers.SerializerMethodField()

    class Meta:
        model = Club
        fields = [
            "id",
            "name",
            "slug",
            "short_name",
            "logo",
            "logo_url",
            "primary_color",
            "secondary_color",
            "founded_year",
            "stadium_name",
            "stadium_capacity",
            "country",
            "city",
            "location",
            "email",
            "phone",
            "website",
            "description",
            "is_public",
            "is_verified",
            "status",
            "status_label",
            "tenant_name",
            "tenant_slug",
            "created_at",
        ]
        read_only_fields = fields

    def get_logo_url(self, obj: Club) -> str:
        """Return the DAM logo URL if available, otherwise fall back to legacy field."""
        try:
            from media_assets.services import MediaAssetService
            from media_assets.constants import OwnerType, AssetCategory

            url = MediaAssetService.get_usage_url(
                owner_type=OwnerType.CLUB,
                owner_id=obj.id,
                role=AssetCategory.LOGO,
            )
            if url:
                return url
        except Exception:
            pass

        try:
            if getattr(obj, "logo"):
                return obj.logo.url
        except Exception:
            pass
        return getattr(obj, "logo", "") or ""

    def get_location(self, obj: Club) -> str:
        return obj.location

    def get_status_label(self, obj: Club) -> str:
        return ClubStatus.LABELS.get(obj.status, obj.status)

    def get_tenant_name(self, obj: Club) -> str:
        return obj.tenant.name if obj.tenant else ""

    def get_tenant_slug(self, obj: Club) -> str:
        return obj.tenant.slug if obj.tenant else ""


class ClubKpisSerializer(serializers.Serializer):
    """Serializer for club KPI statistics."""

    squad_size = serializers.IntegerField()
    staff_count = serializers.IntegerField()
    total_matches = serializers.IntegerField()
    wins = serializers.IntegerField()
    draws = serializers.IntegerField()
    losses = serializers.IntegerField()
    goals_for = serializers.IntegerField()
    goals_against = serializers.IntegerField()
    clean_sheets = serializers.IntegerField()
    active_competitions = serializers.IntegerField()


class ClubMemberSerializer(serializers.ModelSerializer):
    """
    Full serializer for club members (admin management).
    """

    display_name = serializers.SerializerMethodField()
    role_label = serializers.SerializerMethodField()
    position_label = serializers.SerializerMethodField()

    class Meta:
        model = ClubMember
        fields = [
            "id",
            "club",
            "user",
            "full_name",
            "display_name",
            "role",
            "role_label",
            "jersey_number",
            "position",
            "position_label",
            "is_active",
            "joined_at",
            "left_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "club", "display_name", "role_label", "position_label", "created_at", "updated_at"]

    def get_display_name(self, obj: ClubMember) -> str:
        return obj.display_name

    def get_role_label(self, obj: ClubMember) -> str:
        return ClubMemberRole.LABELS.get(obj.role, obj.role)

    def get_position_label(self, obj: ClubMember) -> str:
        return obj.position_label


class ClubSquadMemberSerializer(serializers.ModelSerializer):
    """
    Serializer for squad (player) listings — public view.
    """

    display_name = serializers.SerializerMethodField()
    position_label = serializers.SerializerMethodField()

    class Meta:
        model = ClubMember
        fields = [
            "id",
            "display_name",
            "jersey_number",
            "position",
            "position_label",
            "joined_at",
        ]
        read_only_fields = fields

    def get_display_name(self, obj: ClubMember) -> str:
        return obj.display_name

    def get_position_label(self, obj: ClubMember) -> str:
        return obj.position_label


class ClubStaffSerializer(serializers.ModelSerializer):
    """
    Serializer for staff listings — public view.
    """

    display_name = serializers.SerializerMethodField()
    role_label = serializers.SerializerMethodField()

    class Meta:
        model = ClubMember
        fields = [
            "id",
            "display_name",
            "role",
            "role_label",
            "joined_at",
        ]
        read_only_fields = fields

    def get_display_name(self, obj: ClubMember) -> str:
        return obj.display_name

    def get_role_label(self, obj: ClubMember) -> str:
        return ClubMemberRole.LABELS.get(obj.role, obj.role)
