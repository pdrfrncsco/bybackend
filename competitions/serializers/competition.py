from rest_framework import serializers

from competitions.constants import CompetitionType, CompetitionStatus
from competitions.models import Competition


class CompetitionSerializer(serializers.ModelSerializer):
    type_label = serializers.SerializerMethodField()
    status_label = serializers.SerializerMethodField()

    class Meta:
        model = Competition
        fields = [
            "id",
            "name",
            "slug",
            "competition_type",
            "type_label",
            "season",
            "status",
            "status_label",
            "config",
            "tenant",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "slug",
            "type_label",
            "status_label",
            "tenant",
            "created_at",
            "updated_at",
        ]

    def get_type_label(self, obj: Competition) -> str:
        return CompetitionType.LABELS.get(obj.competition_type, obj.competition_type)

    def get_status_label(self, obj: Competition) -> str:
        return CompetitionStatus.LABELS.get(obj.status, obj.status)


class CompetitionCreateSerializer(serializers.ModelSerializer):
    config = serializers.JSONField(required=False, default=dict)

    class Meta:
        model = Competition
        fields = ["name", "competition_type", "season", "status", "config"]

    def validate_competition_type(self, value: str) -> str:
        valid = {choice[0] for choice in CompetitionType.CHOICES}
        if value not in valid:
            raise serializers.ValidationError("Invalid competition type.")
        return value

    def validate_config(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Config must be a JSON object.")
        return value


class CompetitionUpdateSerializer(serializers.ModelSerializer):
    config = serializers.JSONField(required=False)

    class Meta:
        model = Competition
        fields = ["name", "competition_type", "season", "status", "config"]

    def validate_competition_type(self, value: str) -> str:
        valid = {choice[0] for choice in CompetitionType.CHOICES}
        if value not in valid:
            raise serializers.ValidationError("Invalid competition type.")
        return value

    def validate_config(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Config must be a JSON object.")
        return value


class CompetitionConfigSerializer(serializers.ModelSerializer):
    config = serializers.JSONField(required=False, default=dict)

    class Meta:
        model = Competition
        fields = ["config"]

    def validate_config(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Config must be a JSON object.")
        return value
