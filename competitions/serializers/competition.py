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
            "start_date",
            "end_date",
            "registration_start_date",
            "registration_end_date",
            "description",
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


def _validate_dates(start_date, end_date, reg_start_date, reg_end_date):
    if start_date and end_date and start_date > end_date:
        raise serializers.ValidationError({
            "end_date": "A data de conclusão não pode ser anterior à data de início."
        })
    if reg_start_date and reg_end_date and reg_start_date > reg_end_date:
        raise serializers.ValidationError({
            "registration_end_date": "A data de fim de inscrições não pode ser anterior à data de início."
        })


class CompetitionCreateSerializer(serializers.ModelSerializer):
    config = serializers.JSONField(required=False, default=dict)

    class Meta:
        model = Competition
        fields = [
            "name",
            "competition_type",
            "season",
            "status",
            "start_date",
            "end_date",
            "registration_start_date",
            "registration_end_date",
            "description",
            "config",
        ]

    def validate_competition_type(self, value: str) -> str:
        valid = {choice[0] for choice in CompetitionType.CHOICES}
        if value not in valid:
            raise serializers.ValidationError("Invalid competition type.")
        return value

    def validate_config(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Config must be a JSON object.")
        return value

    def validate(self, attrs):
        _validate_dates(
            attrs.get("start_date"),
            attrs.get("end_date"),
            attrs.get("registration_start_date"),
            attrs.get("registration_end_date"),
        )
        return attrs


class CompetitionUpdateSerializer(serializers.ModelSerializer):
    config = serializers.JSONField(required=False)

    class Meta:
        model = Competition
        fields = [
            "name",
            "competition_type",
            "season",
            "status",
            "start_date",
            "end_date",
            "registration_start_date",
            "registration_end_date",
            "description",
            "config",
        ]

    def validate_competition_type(self, value: str) -> str:
        valid = {choice[0] for choice in CompetitionType.CHOICES}
        if value not in valid:
            raise serializers.ValidationError("Invalid competition type.")
        return value

    def validate_config(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Config must be a JSON object.")
        return value

    def validate(self, attrs):
        start_date = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end_date = attrs.get("end_date", getattr(self.instance, "end_date", None))
        reg_start = attrs.get("registration_start_date", getattr(self.instance, "registration_start_date", None))
        reg_end = attrs.get("registration_end_date", getattr(self.instance, "registration_end_date", None))

        _validate_dates(start_date, end_date, reg_start, reg_end)
        return attrs



class CompetitionConfigSerializer(serializers.ModelSerializer):
    config = serializers.JSONField(required=False, default=dict)

    class Meta:
        model = Competition
        fields = ["config"]

    def validate_config(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Config must be a JSON object.")
        return value
