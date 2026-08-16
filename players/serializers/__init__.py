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
    
    DEPRECATION NOTICE (Compatibility window: 2 sprints):
    - 'email': Use PlayerContact.primary_email via /api/v1/players/{id}/contacts/ instead.
    - 'phone': Use PlayerContact.mobile_phone via /api/v1/players/{id}/contacts/ instead.
    - 'avatar': Use 'profile_photo_url' instead (which references media asset).
    """
    
    age = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    position_label = serializers.SerializerMethodField()
    status_label = serializers.SerializerMethodField()
    current_club = serializers.SerializerMethodField()

    # Prefer values from PlayerFootballProfile when present
    primary_position = serializers.SerializerMethodField()
    shirt_number = serializers.SerializerMethodField()
    height_cm = serializers.SerializerMethodField()
    weight_kg = serializers.SerializerMethodField()
    foot = serializers.SerializerMethodField()
    total_matches = serializers.SerializerMethodField()
    total_goals = serializers.SerializerMethodField()
    total_assists = serializers.SerializerMethodField()

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
            "profile_photo_url",
            "is_public",
            "status",
            "status_label",
            "total_matches",
            "total_goals",
            "total_assists",
            "current_club",
            "created_at",
        ]
        read_only_fields = fields

    def _fp(self, obj: Player):
        """Return football_profile or None (defensive)."""
        try:
            return getattr(obj, "football_profile", None)
        except Exception:
            return None

    def get_age(self, obj: Player) -> int | None:
        return obj.age
    
    def get_full_name(self, obj: Player) -> str:
        return obj.full_name
    
    def get_primary_position(self, obj: Player) -> str | None:
        fp = self._fp(obj)
        return fp.primary_position if fp and fp.primary_position else obj.primary_position

    def get_shirt_number(self, obj: Player) -> int | None:
        fp = self._fp(obj)
        return fp.shirt_number if fp and fp.shirt_number is not None else obj.shirt_number

    def get_height_cm(self, obj: Player) -> int | None:
        fp = self._fp(obj)
        return fp.height_cm if fp and fp.height_cm is not None else obj.height_cm

    def get_weight_kg(self, obj: Player) -> int | None:
        fp = self._fp(obj)
        return fp.weight_kg if fp and fp.weight_kg is not None else obj.weight_kg

    def get_foot(self, obj: Player) -> str | None:
        fp = self._fp(obj)
        return fp.foot if fp and fp.foot else obj.foot

    def get_total_matches(self, obj: Player) -> int:
        fp = self._fp(obj)
        return fp.total_matches if fp is not None else obj.total_matches

    def get_total_goals(self, obj: Player) -> int:
        fp = self._fp(obj)
        return fp.total_goals if fp is not None else obj.total_goals

    def get_total_assists(self, obj: Player) -> int:
        fp = self._fp(obj)
        return fp.total_assists if fp is not None else obj.total_assists

    def get_position_label(self, obj: Player) -> str:
        try:
            # Prefer label for resolved primary_position
            primary = self.get_primary_position(obj)
            return Player.Position(primary).label if primary else ""
        except Exception:
            return primary or ""
    
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


class PlayerDetailSerializer(serializers.ModelSerializer):
    """
    Extended player profile with career summary, videos, documents, and achievements.
    
    Used for: GET /api/v1/players/{id}/ (when ?expand=detail)
    
    DEPRECATION NOTICE (Compatibility window: 2 sprints):
    - 'email': Use PlayerContact.primary_email via /api/v1/players/{id}/contacts/ instead.
    - 'phone': Use PlayerContact.mobile_phone via /api/v1/players/{id}/contacts/ instead.
    - 'avatar': Use 'profile_photo_url' instead (which references media asset).
    """
    
    age = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    position_label = serializers.SerializerMethodField()
    status_label = serializers.SerializerMethodField()
    current_club = serializers.SerializerMethodField()
    career_history = serializers.SerializerMethodField()
    videos = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()
    achievements = serializers.SerializerMethodField()

    # Prefer football_profile values
    primary_position = serializers.SerializerMethodField()
    shirt_number = serializers.SerializerMethodField()
    height_cm = serializers.SerializerMethodField()
    weight_kg = serializers.SerializerMethodField()
    foot = serializers.SerializerMethodField()
    total_matches = serializers.SerializerMethodField()
    total_goals = serializers.SerializerMethodField()
    total_assists = serializers.SerializerMethodField()

    class Meta:
        model = Player
        fields = [
            "id",
            "slug",
            "first_name",
            "last_name",
            "full_name",
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
            "profile_photo_url",
            "is_public",
            "status",
            "status_label",
            "total_matches",
            "total_goals",
            "total_assists",
            "current_club",
            "career_history",
            "videos",
            "documents",
            "achievements",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def _fp(self, obj: Player):
        try:
            return getattr(obj, "football_profile", None)
        except Exception:
            return None

    def get_age(self, obj: Player) -> int | None:
        return obj.age
    
    def get_full_name(self, obj: Player) -> str:
        return obj.full_name

    def get_primary_position(self, obj: Player) -> str | None:
        fp = self._fp(obj)
        return fp.primary_position if fp and fp.primary_position else obj.primary_position

    def get_shirt_number(self, obj: Player) -> int | None:
        fp = self._fp(obj)
        return fp.shirt_number if fp and fp.shirt_number is not None else obj.shirt_number

    def get_height_cm(self, obj: Player) -> int | None:
        fp = self._fp(obj)
        return fp.height_cm if fp and fp.height_cm is not None else obj.height_cm

    def get_weight_kg(self, obj: Player) -> int | None:
        fp = self._fp(obj)
        return fp.weight_kg if fp and fp.weight_kg is not None else obj.weight_kg

    def get_foot(self, obj: Player) -> str | None:
        fp = self._fp(obj)
        return fp.foot if fp and fp.foot else obj.foot

    def get_total_matches(self, obj: Player) -> int:
        fp = self._fp(obj)
        return fp.total_matches if fp is not None else obj.total_matches

    def get_total_goals(self, obj: Player) -> int:
        fp = self._fp(obj)
        return fp.total_goals if fp is not None else obj.total_goals

    def get_total_assists(self, obj: Player) -> int:
        fp = self._fp(obj)
        return fp.total_assists if fp is not None else obj.total_assists

    def get_position_label(self, obj: Player) -> str:
        try:
            primary = self.get_primary_position(obj)
            return Player.Position(primary).label if primary else ""
        except Exception:
            return primary or ""
    
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

    def get_profile_photo_url(self, obj: Player) -> str | None:
        return obj.profile_photo_url
    
    def get_videos(self, obj: Player) -> list:
        """Return player's published videos."""
        from players.models import PlayerVideo
        videos = obj.videos.filter(
            status=PlayerVideo.VideoStatus.PUBLISHED
        ).order_by("-is_featured", "order", "-created_at")[:10]
        return [
            {
                "id": video.id,
                "title": video.title,
                "video_type": video.video_type,
                "video_type_label": video.get_video_type_display(),
                "url": video.url,
                "thumbnail": video.thumbnail,
                "duration_seconds": video.duration_seconds,
                "is_featured": video.is_featured,
                "created_at": video.created_at,
            }
            for video in videos
        ]
    
    def get_documents(self, obj: Player) -> list:
        """Return player's public documents."""
        from players.models import PlayerDocument
        documents = obj.documents.filter(
            is_private=False
        ).order_by("-created_at")[:10]
        return [
            {
                "id": doc.id,
                "title": doc.title,
                "category": doc.category,
                "category_label": doc.get_category_display(),
                "asset_url": doc.asset.public_url if doc.asset else None,
                "is_valid": doc.is_valid,
                "created_at": doc.created_at,
            }
            for doc in documents
        ]
    
    def get_achievements(self, obj: Player) -> list:
        """Return player's achievements."""
        achievements = obj.achievements.filter(is_verified=True).order_by("-date_achieved", "-created_at")[:20]
        return [
            {
                "id": achievement.id,
                "title": achievement.title,
                "achievement_type": achievement.achievement_type,
                "achievement_type_label": achievement.get_achievement_type_display(),
                "level": achievement.level,
                "level_label": achievement.get_level_display(),
                "date_achieved": achievement.date_achieved,
                "year": achievement.year,
                "season": achievement.season,
                "club_name": achievement.club.name if achievement.club else None,
                "competition_name": achievement.competition.name if achievement.competition else None,
                "trophy_image": achievement.trophy_image,
                "is_verified": achievement.is_verified,
            }
            for achievement in achievements
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
