from rest_framework import serializers

from players.models import PlayerPrivacySettings


class PlayerPrivacySettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerPrivacySettings
        fields = [
            "player",
            "profile_visibility",
            "contact_visibility",
            "contract_visibility",
            "salary_visibility",
            "medical_visibility",
            "documents_visibility",
            "statistics_visibility",
        ]
        read_only_fields = ["player"]
