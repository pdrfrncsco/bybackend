"""
BOLAYETU — Club Serializers

Serializers for club endpoints.
These handle INPUT validation and OUTPUT serialization.
No business logic lives here.
"""

from rest_framework import serializers

from clubs.constants import ClubMemberRole, ClubStatus
from clubs.models import Club, ClubMember


class ClubSerializer(serializers.ModelSerializer):
    """
    Full club serializer for authenticated users (club admin/management).
    """

    logo_url = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    status_label = serializers.SerializerMethodField()
    tenant_name = serializers.SerializerMethodField()
    tenant_slug = serializers.SerializerMethodField()
    # Expose affiliation request summary (if any) so frontend can show banners/CTA
    affiliation_request_status = serializers.SerializerMethodField()
    affiliation_request_id = serializers.SerializerMethodField()

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
            "affiliation_request_status",
            "affiliation_request_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "slug",
            "logo_url",
            "location",
            "status_label",
            "tenant_name",
            "tenant_slug",
            "affiliation_request_status",
            "affiliation_request_id",
            "created_at",
            "updated_at",
        ]

    def get_logo_url(self, obj: Club) -> str:
        """Return the DAM logo URL for this club, if any."""
        try:
            from media_assets.constants import AssetCategory, OwnerType
            from media_assets.services import MediaAssetService

            url = (
                MediaAssetService.get_usage_url(
                    owner_type=OwnerType.CLUB,
                    owner_id=obj.id,
                    role=AssetCategory.LOGO,
                )
                or ""
            )
            if url:
                request = self.context.get("request")
                if request:
                    return request.build_absolute_uri(url)
            return url
        except Exception:
            return ""

    def get_location(self, obj: Club) -> str:
        return obj.location

    def get_status_label(self, obj: Club) -> str:
        return ClubStatus.LABELS.get(obj.status, obj.status)

    def get_tenant_name(self, obj: Club) -> str:
        return obj.tenant.name if obj.tenant else ""

    def get_tenant_slug(self, obj: Club) -> str:
        return obj.tenant.slug if obj.tenant else ""


    def get_affiliation_request_status(self, obj: Club) -> str | None:
        # Return the linked affiliation request status if present (draft, pending, approved, rejected)
        try:
            req = getattr(obj, 'affiliation_request', None)
            return req.status if req is not None else None
        except Exception:
            return None

    def get_affiliation_request_id(self, obj: Club) -> str | None:
        try:
            req = getattr(obj, 'affiliation_request', None)
            return str(req.id) if req is not None else None
        except Exception:
            return None

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
        """Return the DAM logo URL for this club, if any."""
        try:
            from media_assets.constants import AssetCategory, OwnerType
            from media_assets.services import MediaAssetService

            url = (
                MediaAssetService.get_usage_url(
                    owner_type=OwnerType.CLUB,
                    owner_id=obj.id,
                    role=AssetCategory.LOGO,
                )
                or ""
            )
            if url:
                request = self.context.get("request")
                if request:
                    return request.build_absolute_uri(url)
            return url
        except Exception:
            return ""

    def get_location(self, obj: Club) -> str:
        return obj.location

    def get_status_label(self, obj: Club) -> str:
        return ClubStatus.LABELS.get(obj.status, obj.status)

    def get_tenant_name(self, obj: Club) -> str:
        return obj.tenant.name if obj.tenant else ""

    def get_tenant_slug(self, obj: Club) -> str:
        return obj.tenant.slug if obj.tenant else ""


class ClubLogoUploadSerializer(serializers.Serializer):
    """Serializer describing the multipart payload for club logo uploads."""

    logo = serializers.ImageField(help_text="Image file (JPEG, PNG, WebP or SVG, max 5MB).")


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
    avatar = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    status_label = serializers.SerializerMethodField()

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
            "status",
            "status_label",
            "avatar",
            "joined_at",
            "left_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "club", "display_name", "role_label", "position_label", "status", "status_label", "avatar", "created_at", "updated_at"]

    def get_display_name(self, obj: ClubMember) -> str:
        return obj.display_name

    def get_role_label(self, obj: ClubMember) -> str:
        return ClubMemberRole.LABELS.get(obj.role, obj.role)

    def get_position_label(self, obj: ClubMember) -> str:
        return obj.position_label

    def get_status(self, obj: ClubMember) -> str:
        return "active" if obj.is_active else "inactive"

    def get_status_label(self, obj: ClubMember) -> str:
        return "Ativo" if obj.is_active else "Inativo"

    def get_avatar(self, obj: ClubMember) -> str | None:
        if obj.user:
            url = getattr(obj.user, "avatar", None)
            if url:
                request = self.context.get("request") if hasattr(self, "context") and self.context else None
                if request and not url.startswith(("http://", "https://", "data:", "blob:")):
                    return request.build_absolute_uri(url)
                return url
        return None


class ClubSquadMemberSerializer(serializers.ModelSerializer):
    """
    Serializer for squad (player) listings — public view.

    NOTE: Now uses PlayerRegistration instead of ClubMember.
    """

    display_name = serializers.SerializerMethodField()
    position = serializers.SerializerMethodField()
    position_label = serializers.SerializerMethodField()
    jersey_number = serializers.IntegerField(source="shirt_number", read_only=True)
    joined_at = serializers.DateField(source="joined_date", read_only=True)
    player_id = serializers.SerializerMethodField()
    player_slug = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    status_label = serializers.SerializerMethodField()
    nationality = serializers.SerializerMethodField()
    date_of_birth = serializers.SerializerMethodField()
    height_cm = serializers.SerializerMethodField()
    weight_kg = serializers.SerializerMethodField()
    foot = serializers.SerializerMethodField()
    matches_played = serializers.SerializerMethodField()
    goals = serializers.SerializerMethodField()
    assists = serializers.SerializerMethodField()
    yellow_cards = serializers.SerializerMethodField()
    red_cards = serializers.SerializerMethodField()

    class Meta:
        model = ClubMember  # Keep for backward compatibility, but fields come from PlayerRegistration
        fields = [
            "id",
            "player_id",
            "player_slug",
            "display_name",
            "jersey_number",
            "position",
            "position_label",
            "joined_at",
            "avatar",
            "status",
            "status_label",
            "nationality",
            "date_of_birth",
            "height_cm",
            "weight_kg",
            "foot",
            "matches_played",
            "goals",
            "assists",
            "yellow_cards",
            "red_cards",
        ]
        read_only_fields = fields

    def get_player_id(self, obj) -> str | None:
        """Returns the Player UUID for lineup submission."""
        if hasattr(obj, "player") and obj.player:
            return str(obj.player.id)
        return None

    def get_player_slug(self, obj) -> str | None:
        """Returns the Player slug."""
        if hasattr(obj, "player") and obj.player:
            return getattr(obj.player, "slug", None)
        return None

    def get_display_name(self, obj) -> str:
        """Returns the player's full name from the PlayerRegistration."""
        if hasattr(obj, "player") and obj.player:
            return obj.player.full_name
        # Fallback for old ClubMember records
        return obj.display_name if hasattr(obj, "display_name") else str(obj)

    def get_avatar(self, obj) -> str | None:
        """Returns the player's avatar or profile photo URL."""
        if hasattr(obj, "player") and obj.player:
            player = obj.player
            url = getattr(player, "profile_photo_url", None) or getattr(player, "avatar", None)
            if not url:
                try:
                    from media_assets.constants import AssetCategory, OwnerType
                    from media_assets.services import MediaAssetService

                    url = MediaAssetService.get_usage_url(
                        owner_type=OwnerType.PLAYER,
                        owner_id=player.id,
                        role=AssetCategory.AVATAR,
                    )
                except Exception:
                    url = None
            if url:
                request = self.context.get("request") if hasattr(self, "context") and self.context else None
                if request and not url.startswith(("http://", "https://", "data:", "blob:")):
                    return request.build_absolute_uri(url)
                return url
        return None

    def get_status(self, obj) -> str:
        if hasattr(obj, "status") and obj.status:
            return obj.status
        if hasattr(obj, "is_active"):
            return "registered" if obj.is_active else "inactive"
        return "registered"

    def get_status_label(self, obj) -> str:
        if hasattr(obj, "get_status_display"):
            return obj.get_status_display()
        if hasattr(obj, "is_active"):
            return "Ativo" if obj.is_active else "Inativo"
        return "Registado"

    def get_position(self, obj) -> str:
        """Returns the player's position from the PlayerRegistration."""
        if hasattr(obj, "player") and obj.player:
            return obj.player.primary_position
        return getattr(obj, "position", "") or ""

    def get_position_label(self, obj) -> str:
        """Returns the player's position label from the PlayerRegistration."""
        if hasattr(obj, "player") and obj.player:
            try:
                from players.models import Player

                return Player.Position(obj.player.primary_position).label if obj.player.primary_position else ""
            except ValueError:
                return obj.player.primary_position or ""
        # Fallback for old ClubMember records
        return getattr(obj, "position_label", "") or ""

    def get_nationality(self, obj) -> str | None:
        if hasattr(obj, "player") and obj.player:
            return getattr(obj.player, "nationality", None)
        return None

    def get_date_of_birth(self, obj) -> str | None:
        if hasattr(obj, "player") and obj.player and obj.player.date_of_birth:
            return str(obj.player.date_of_birth)
        return None

    def get_height_cm(self, obj) -> int | None:
        if hasattr(obj, "player") and obj.player:
            return getattr(obj.player, "height_cm", None)
        return None

    def get_weight_kg(self, obj) -> int | None:
        if hasattr(obj, "player") and obj.player:
            return getattr(obj.player, "weight_kg", None)
        return None

    def get_foot(self, obj) -> str | None:
        if hasattr(obj, "player") and obj.player:
            return getattr(obj.player, "foot", None)
        return None

    def get_matches_played(self, obj) -> int:
        return getattr(obj, "matches_played", 0) or 0

    def get_goals(self, obj) -> int:
        return getattr(obj, "goals", 0) or 0

    def get_assists(self, obj) -> int:
        return getattr(obj, "assists", 0) or 0

    def get_yellow_cards(self, obj) -> int:
        return getattr(obj, "yellow_cards", 0) or 0

    def get_red_cards(self, obj) -> int:
        return getattr(obj, "red_cards", 0) or 0


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
