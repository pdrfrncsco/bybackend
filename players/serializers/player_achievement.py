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
    trophy_image = serializers.SerializerMethodField()
    certificate_url = serializers.SerializerMethodField()

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

    def get_trophy_image(self, obj: PlayerAchievement) -> str | None:
        if obj.trophy_asset:
            return obj.trophy_asset.public_url
        return obj.trophy_image

    def get_certificate_url(self, obj: PlayerAchievement) -> str | None:
        if obj.certificate_asset:
            return obj.certificate_asset.public_url
        return obj.certificate_url


class PlayerAchievementCreateSerializer(serializers.Serializer):
    """
    Serializer for creating a new player achievement.

    Accepts file uploads or external URLs for trophy/certificate media.
    """

    title = serializers.CharField(max_length=255)
    achievement_type = serializers.ChoiceField(choices=PlayerAchievement.AchievementType.choices)
    level = serializers.ChoiceField(choices=PlayerAchievement.AchievementLevel.choices)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    date_achieved = serializers.DateField(required=False, allow_null=True)
    season = serializers.CharField(required=False, allow_blank=True, default="")
    competition = serializers.UUIDField(required=False, allow_null=True)
    club = serializers.UUIDField(required=False, allow_null=True)
    trophy_image = serializers.FileField(required=False)
    certificate = serializers.FileField(required=False)
    trophy_image_url = serializers.URLField(required=False, allow_blank=True, default="")
    certificate_url = serializers.URLField(required=False, allow_blank=True, default="")
    stats_snapshot = serializers.JSONField(required=False, allow_null=True)

    def validate(self, data):
        if data.get("trophy_image") and data.get("trophy_image_url"):
            raise serializers.ValidationError(
                "Provide either trophy_image file or trophy_image_url, not both."
            )
        if data.get("certificate") and data.get("certificate_url"):
            raise serializers.ValidationError(
                "Provide either certificate file or certificate_url, not both."
            )
        return data


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

    pass
