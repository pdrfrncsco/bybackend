"""
BOLAYETU — Player Serializers

Serializers for Player endpoints (public API).
"""

from rest_framework import serializers

from players.models import Player, PlayerRegistration


class PlayerSerializer(serializers.ModelSerializer):
    """
    Public player profile serializer.
    
    Used for: GET /api/v1/players/ (list), GET /api/v1/players/{id}/ (detail)
    """
    
    age = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    position_label = serializers.SerializerMethodField()
    status_label = serializers.SerializerMethodField()
    
    class Meta:
        model = Player
        fields = [
            "id",
            "slug",
            "first_name",
            "last_name",
            "full_name",
            "email",
            "date_of_birth",
            "age",
            "nationality",
            "height_cm",
            "weight_kg",
            "foot",
            "primary_position",
            "position_label",
            "shirt_number",
            "bio",
            "avatar",
            "status",
            "status_label",
            "total_matches",
            "total_goals",
            "total_assists",
            "created_at",
        ]
        read_only_fields = fields
    
    def get_age(self, obj: Player) -> int | None:
        return obj.age
    
    def get_full_name(self, obj: Player) -> str:
        return obj.full_name
    
    def get_position_label(self, obj: Player) -> str:
        try:
            return Player.Position(obj.primary_position).label if obj.primary_position else ""
        except ValueError:
            return obj.primary_position or ""
    
    def get_status_label(self, obj: Player) -> str:
        try:
            return Player.PlayerStatus(obj.status).label if obj.status else ""
        except ValueError:
            return obj.status or ""


class PlayerDetailSerializer(serializers.ModelSerializer):
    """
    Extended player profile with career summary.
    
    Used for: GET /api/v1/players/{id}/ (when ?expand=detail)
    """
    
    age = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    position_label = serializers.SerializerMethodField()
    status_label = serializers.SerializerMethodField()
    current_club = serializers.SerializerMethodField()
    career_history = serializers.SerializerMethodField()
    
    class Meta:
        model = Player
        fields = [
            "id",
            "slug",
            "first_name",
            "last_name",
            "full_name",
            "email",
            "phone",
            "date_of_birth",
            "age",
            "nationality",
            "height_cm",
            "weight_kg",
            "foot",
            "primary_position",
            "position_label",
            "shirt_number",
            "bio",
            "avatar",
            "status",
            "status_label",
            "total_matches",
            "total_goals",
            "total_assists",
            "current_club",
            "career_history",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
    
    def get_age(self, obj: Player) -> int | None:
        return obj.age
    
    def get_full_name(self, obj: Player) -> str:
        return obj.full_name
    
    def get_position_label(self, obj: Player) -> str:
        try:
            return Player.Position(obj.primary_position).label if obj.primary_position else ""
        except ValueError:
            return obj.primary_position or ""
    
    def get_status_label(self, obj: Player) -> str:
        try:
            return Player.PlayerStatus(obj.status).label if obj.status else ""
        except ValueError:
            return obj.status or ""
    
    def get_current_club(self, obj: Player) -> dict | None:
        """Return the player's current club (if registered)."""
        current = obj.registrations.filter(status__in=["registered", "loaned"]).select_related("club").first()
        if current:
            return {
                "id": current.club.id,
                "name": current.club.name,
                "slug": current.club.slug,
                "registered_since": current.joined_date,
                "shirt_number": current.shirt_number,
            }
        return None
    
    def get_career_history(self, obj: Player) -> list:
        """Return player's career registrations."""
        registrations = obj.registrations.select_related("club").order_by("-joined_date")
        return [
            {
                "club": registration.club.name,
                "club_slug": registration.club.slug,
                "joined": registration.joined_date,
                "left": registration.left_date,
                "status": registration.get_status_display(),
                "matches": registration.matches_played,
                "goals": registration.goals,
                "assists": registration.assists,
            }
            for registration in registrations
        ]


class PlayerRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for player registrations (club-level view).
    
    Used for: Club squad listing
    """
    
    player_name = serializers.CharField(source="player.full_name", read_only=True)
    player_slug = serializers.CharField(source="player.slug", read_only=True)
    position = serializers.CharField(source="player.primary_position", read_only=True)
    position_label = serializers.SerializerMethodField()
    status_label = serializers.SerializerMethodField()
    
    class Meta:
        model = PlayerRegistration
        fields = [
            "id",
            "player",
            "player_name",
            "player_slug",
            "shirt_number",
            "position",
            "position_label",
            "joined_date",
            "left_date",
            "status",
            "status_label",
            "matches_played",
            "goals",
            "assists",
            "yellow_cards",
            "red_cards",
        ]
        read_only_fields = fields
    
    def get_position_label(self, obj: PlayerRegistration) -> str:
        try:
            return Player.Position(obj.player.primary_position).label if obj.player.primary_position else ""
        except ValueError:
            return obj.player.primary_position or ""
    
    def get_status_label(self, obj: PlayerRegistration) -> str:
        return obj.get_status_display()
