"""
PlayerTrainingHistory Serializers
"""

from rest_framework import serializers
from players.models import PlayerTrainingHistory


class PlayerTrainingHistorySerializer(serializers.ModelSerializer):
    """Full serializer for PlayerTrainingHistory."""

    player_name = serializers.CharField(source="player.full_name", read_only=True)
    club_name = serializers.SerializerMethodField()
    duration_years = serializers.SerializerMethodField()
    training_category_label = serializers.SerializerMethodField()

    class Meta:
        model = PlayerTrainingHistory
        fields = [
            "id",
            "player",
            "player_name",
            "club",
            "club_name",
            "academy_name",
            "country",
            "training_category",
            "training_category_label",
            "start_date",
            "end_date",
            "duration_years",
            "verified",
            "verified_by",
            "verified_at",
            "training_certificate",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "verified",
            "verified_by",
            "verified_at",
            "created_at",
            "updated_at",
        ]

    def get_club_name(self, obj):
        return obj.club.name if obj.club else obj.academy_name

    def get_duration_years(self, obj):
        return round(obj.duration_years, 2)

    def get_training_category_label(self, obj):
        return obj.get_training_category_display()


class PlayerTrainingHistoryListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing training history."""

    club_name = serializers.SerializerMethodField()
    duration_years = serializers.SerializerMethodField()
    training_category_label = serializers.SerializerMethodField()

    class Meta:
        model = PlayerTrainingHistory
        fields = [
            "id",
            "club_name",
            "country",
            "training_category",
            "training_category_label",
            "start_date",
            "end_date",
            "duration_years",
            "verified",
        ]

    def get_club_name(self, obj):
        return obj.club.name if obj.club else obj.academy_name

    def get_duration_years(self, obj):
        return round(obj.duration_years, 2)

    def get_training_category_label(self, obj):
        return obj.get_training_category_display()


class PlayerTrainingHistoryCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating training history entries."""

    class Meta:
        model = PlayerTrainingHistory
        fields = [
            "player",
            "club",
            "academy_name",
            "country",
            "training_category",
            "start_date",
            "end_date",
            "training_certificate",
            "notes",
        ]

    def validate(self, data):
        """Ensure either club or academy_name is provided."""
        club = data.get("club")
        academy_name = data.get("academy_name", "")

        if not club and not academy_name:
            raise serializers.ValidationError(
                "Either club or academy_name must be provided."
            )

        # Validate dates
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        if end_date and start_date and end_date < start_date:
            raise serializers.ValidationError(
                "end_date must be after start_date."
            )

        return data


class TrainingCompensationDataSerializer(serializers.Serializer):
    """Serializer for training compensation calculation data."""

    total_years = serializers.FloatField()
    clubs = serializers.ListField(
        child=serializers.DictField()
    )
