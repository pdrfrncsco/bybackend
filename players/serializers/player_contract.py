"""
PlayerContract Serializers
"""

from rest_framework import serializers
from players.models import PlayerContract


class PlayerContractSerializer(serializers.ModelSerializer):
    """Full serializer for PlayerContract (admin/detailed view)."""

    player_name = serializers.CharField(source="player.full_name", read_only=True)
    club_name = serializers.CharField(source="club.name", read_only=True)
    is_active = serializers.SerializerMethodField()
    is_fully_signed = serializers.SerializerMethodField()

    class Meta:
        model = PlayerContract
        fields = [
            "id",
            "player",
            "player_name",
            "club",
            "club_name",
            "contract_type",
            "status",
            "start_date",
            "end_date",
            "signed_date",
            "salary",
            "currency",
            "bonuses",
            "release_clause",
            "has_image_rights",
            "option_year",
            "termination_clause",
            "contract_document",
            "signed_by_player",
            "signed_by_club",
            "verified_at",
            "verified_by",
            "is_active",
            "is_fully_signed",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "verified_at",
            "verified_by",
            "signed_date",
        ]

    def get_is_active(self, obj):
        return obj.is_active

    def get_is_fully_signed(self, obj):
        return obj.is_fully_signed


class PlayerContractListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing contracts."""

    player_name = serializers.CharField(source="player.full_name", read_only=True)
    club_name = serializers.CharField(source="club.name", read_only=True)
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = PlayerContract
        fields = [
            "id",
            "player_name",
            "club_name",
            "contract_type",
            "status",
            "start_date",
            "end_date",
            "salary",
            "currency",
            "is_active",
        ]

    def get_is_active(self, obj):
        return obj.is_active


class PlayerContractCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating contracts."""

    class Meta:
        model = PlayerContract
        fields = [
            "player",
            "club",
            "tenant",
            "contract_type",
            "start_date",
            "end_date",
            "salary",
            "currency",
            "bonuses",
            "release_clause",
            "has_image_rights",
            "option_year",
            "termination_clause",
            "contract_document",
        ]

    def validate(self, data):
        """Ensure end_date is after start_date."""
        if data["end_date"] <= data["start_date"]:
            raise serializers.ValidationError("end_date must be after start_date.")
        return data
