"""
Agent and PlayerAgentRelationship Serializers
"""

from rest_framework import serializers
from players.models import Agent, PlayerAgentRelationship


class AgentSerializer(serializers.ModelSerializer):
    """Full serializer for Agent."""

    class Meta:
        model = Agent
        fields = [
            "id",
            "name",
            "agency_name",
            "agency_type",
            "license_number",
            "fifa_agent_id",
            "country",
            "email",
            "phone",
            "website",
            "address",
            "city",
            "postal_code",
            "is_active",
            "verified",
            "verified_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "verified_at",
        ]


class AgentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing agents."""

    class Meta:
        model = Agent
        fields = [
            "id",
            "name",
            "agency_name",
            "agency_type",
            "country",
            "email",
            "phone",
            "is_active",
            "verified",
        ]


class PlayerAgentRelationshipSerializer(serializers.ModelSerializer):
    """Full serializer for PlayerAgentRelationship."""

    player_name = serializers.CharField(source="player.full_name", read_only=True)
    agent_name = serializers.CharField(source="agent.name", read_only=True)
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = PlayerAgentRelationship
        fields = [
            "id",
            "player",
            "player_name",
            "agent",
            "agent_name",
            "tenant",
            "start_date",
            "end_date",
            "status",
            "commission_rate",
            "representation_agreement",
            "notes",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]

    def get_is_active(self, obj):
        return obj.is_active


class PlayerAgentRelationshipListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing agent relationships."""

    player_name = serializers.CharField(source="player.full_name", read_only=True)
    agent_name = serializers.CharField(source="agent.name", read_only=True)
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = PlayerAgentRelationship
        fields = [
            "id",
            "player_name",
            "agent_name",
            "start_date",
            "end_date",
            "status",
            "commission_rate",
            "is_active",
        ]

    def get_is_active(self, obj):
        return obj.is_active
