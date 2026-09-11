from rest_framework import serializers
from players.models import LegalGuardian


class LegalGuardianSerializer(serializers.ModelSerializer):
    class Meta:
        model = LegalGuardian
        fields = [
            "id",
            "name",
            "relationship",
            "document_number",
            "phone",
            "email",
            "address",
            "consent_status",
            "consent_document",
            "consent_given_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
