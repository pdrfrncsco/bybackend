"""
Player Medical Profile Serializers

Serializers for medical profile and document endpoints.
"""

from rest_framework import serializers
from players.models import PlayerMedicalProfile, MedicalDocument


class PlayerMedicalProfileSerializer(serializers.ModelSerializer):
    """Full serializer for PlayerMedicalProfile."""

    player_name = serializers.CharField(source="player.full_name", read_only=True)
    medical_status_label = serializers.SerializerMethodField()
    blood_type_label = serializers.SerializerMethodField()
    is_fit_to_play = serializers.ReadOnlyField()
    needs_medical_exam = serializers.ReadOnlyField()

    class Meta:
        model = PlayerMedicalProfile
        fields = [
            "id",
            "player",
            "player_name",
            "blood_type",
            "blood_type_label",
            "medical_status",
            "medical_status_label",
            "injury_status",
            "medical_clearance",
            "fitness_status",
            "medical_notes",
            "allergies",
            "current_medications",
            "medical_conditions",
            "last_medical_exam",
            "next_medical_exam",
            "is_fit_to_play",
            "needs_medical_exam",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_medical_status_label(self, obj):
        return obj.get_medical_status_display()

    def get_blood_type_label(self, obj):
        return obj.get_blood_type_display()


class PlayerMedicalProfileLimitedSerializer(serializers.ModelSerializer):
    """Limited serializer for non-medical staff (public view).

    Excludes sensitive medical information.
    """

    player_name = serializers.CharField(source="player.full_name", read_only=True)
    medical_status_label = serializers.SerializerMethodField()
    is_fit_to_play = serializers.ReadOnlyField()

    class Meta:
        model = PlayerMedicalProfile
        fields = [
            "id",
            "player_name",
            "medical_status",
            "medical_status_label",
            "medical_clearance",
            "is_fit_to_play",
        ]

    def get_medical_status_label(self, obj):
        return obj.get_medical_status_display()


class MedicalDocumentSerializer(serializers.ModelSerializer):
    """Full serializer for MedicalDocument."""

    player_name = serializers.CharField(source="player.full_name", read_only=True)
    document_type_label = serializers.SerializerMethodField()
    verification_status_label = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    is_valid = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()

    class Meta:
        model = MedicalDocument
        fields = [
            "id",
            "player",
            "player_name",
            "document_type",
            "document_type_label",
            "title",
            "description",
            "file",
            "file_url",
            "issued_at",
            "expires_at",
            "verification_status",
            "verification_status_label",
            "verified_by",
            "verified_at",
            "is_confidential",
            "is_valid",
            "is_expired",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "verification_status",
            "verified_by",
            "verified_at",
            "created_at",
            "updated_at",
        ]

    def get_document_type_label(self, obj):
        return obj.get_document_type_display()

    def get_verification_status_label(self, obj):
        return obj.get_verification_status_display()

    def get_file_url(self, obj):
        if obj.file:
            return obj.file.public_url
        return None


class MedicalDocumentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating medical documents."""

    class Meta:
        model = MedicalDocument
        fields = [
            "player",
            "document_type",
            "title",
            "description",
            "file",
            "issued_at",
            "expires_at",
            "is_confidential",
        ]


class MedicalHistorySerializer(serializers.Serializer):
    """Serializer for complete medical history response."""

    profile = PlayerMedicalProfileSerializer()
    documents = MedicalDocumentSerializer(many=True)
    is_fit_to_play = serializers.BooleanField()
    pending_exams = serializers.BooleanField()
