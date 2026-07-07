"""
BOLAYETU — Player Achievement Serializers

Serializers for player achievement endpoints.
"""

from rest_framework import serializers

from players.models import PlayerAchievement


class PlayerAchievementSerializer(serializers.ModelSerializer):
    """
    Serializer for viewing player achievements.
    
    Used for: GET /api/v1/players/{slug}/achievements/
    """
    
    achievement_type_label = serializers.SerializerMethodField()
    level_label = serializers.SerializerMethodField()
    year = serializers.ReadOnlyField()
    competition_name = serializers.CharField(source="competition.name", read_only=True)
    club_name = serializers.CharField(source="club.name", read_only=True)
    
    class Meta:
        model = PlayerAchievement
        fields = [
            "id",
            "title",
            "achievement_type",
            "achievement_type_label",
            "level",
            "level_label",
            "description",
            "date_achieved",
            "year",
            "season",
            "competition",
            "competition_name",
            "club",
            "club_name",
            "trophy_image",
            "certificate_url",
            "stats_snapshot",
            "is_verified",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "is_verified",
            "created_at",
            "updated_at",
        ]
    
    def get_achievement_type_label(self, obj: PlayerAchievement) -> str:
        return obj.get_achievement_type_display()
    
    def get_level_label(self, obj: PlayerAchievement) -> str:
        return obj.get_level_display()


class PlayerAchievementCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new player achievement.
    
    Used for: POST /api/v1/players/{slug}/achievements/
    """
    
    class Meta:
        model = PlayerAchievement
        fields = [
            "title",
            "achievement_type",
            "level",
            "description",
            "date_achieved",
            "season",
            "competition",
            "club",
            "trophy_image",
            "certificate_url",
            "stats_snapshot",
        ]


class PlayerAchievementUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating a player achievement.
    
    Used for: PATCH /api/v1/players/{slug}/achievements/{id}/
    """
    
    class Meta:
        model = PlayerAchievement
        fields = [
            "title",
            "achievement_type",
            "level",
            "description",
            "date_achieved",
            "season",
            "competition",
            "club",
            "trophy_image",
            "certificate_url",
            "stats_snapshot",
        ]


class PlayerAchievementVerifySerializer(serializers.Serializer):
    """
    Serializer for verifying a player achievement.
    
    Used for: POST /api/v1/players/{slug}/achievements/{id}/verify/
    """
    
    pass  # No additional fields needed - verification is a simple action
