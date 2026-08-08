from rest_framework import serializers
from players.models import PlayerContact, EmergencyContact


class PlayerContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerContact
        fields = [
            "id",
            "primary_email",
            "secondary_email",
            "mobile_phone",
            "secondary_phone",
            "country_code",
            "address",
            "city",
            "province",
            "postal_code",
            "country",
        ]
        read_only_fields = ["id"]


class EmergencyContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyContact
        fields = ["id", "name", "relationship", "phone", "email", "country"]
        read_only_fields = ["id"]
