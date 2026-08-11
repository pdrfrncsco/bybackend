"""
Agent and PlayerAgentRelationship Views

CRUD endpoints for agents and agent-player relationships.
"""

import logging

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers

from players.models import Agent, PlayerAgentRelationship, Player
from players.serializers.player_agent import (
    AgentSerializer,
    AgentListSerializer,
    PlayerAgentRelationshipSerializer,
    PlayerAgentRelationshipListSerializer,
)

logger = logging.getLogger("players")


class AgentListCreateView(generics.ListCreateAPIView):
    """List and create agents.
    
    GET /agents/ — List all agents
    POST /agents/ — Create new agent
    """
    
    permission_classes = [IsAuthenticated]
    queryset = Agent.objects.all().order_by("name")

    def get_serializer_class(self):
        if self.request.method == "GET":
            return AgentListSerializer
        return AgentSerializer


class AgentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete an agent.
    
    GET /agents/{agent_id}/ — Get agent
    PATCH /agents/{agent_id}/ — Update agent
    DELETE /agents/{agent_id}/ — Delete agent
    """
    
    permission_classes = [IsAuthenticated]
    queryset = Agent.objects.all()
    serializer_class = AgentSerializer
    lookup_field = "id"


class PlayerAgentRelationshipListCreateView(generics.ListCreateAPIView):
    """List and create player-agent relationships.
    
    GET /players/{player_id}/agents/ — List agent relationships for a player
    POST /players/{player_id}/agents/ — Link player to agent
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = PlayerAgentRelationshipSerializer

    def get_queryset(self):
        player_id = self.kwargs.get("player_id")
        if player_id:
            return PlayerAgentRelationship.objects.filter(
                player_id=player_id
            ).select_related("player", "agent").order_by("-start_date")
        return PlayerAgentRelationship.objects.none()

    def get_serializer_class(self):
        if self.request.method == "GET":
            return PlayerAgentRelationshipListSerializer
        return PlayerAgentRelationshipSerializer

    def perform_create(self, serializer):
        player_id = self.kwargs.get("player_id")
        try:
            player = Player.objects.get(id=player_id)
            serializer.save(player=player)
            logger.info(
                "Agent linked to player: %s → %s",
                player.full_name,
                serializer.validated_data["agent"].name,
            )
        except Player.DoesNotExist:
            raise serializers.ValidationError({"player_id": "Player not found."})


class PlayerAgentRelationshipDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a player-agent relationship.
    
    GET /players/{player_id}/agents/{relationship_id}/ — Get relationship
    PATCH /players/{player_id}/agents/{relationship_id}/ — Update relationship
    DELETE /players/{player_id}/agents/{relationship_id}/ — Delete relationship
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = PlayerAgentRelationshipSerializer
    lookup_field = "id"

    def get_queryset(self):
        player_id = self.kwargs.get("player_id")
        return PlayerAgentRelationship.objects.filter(
            player_id=player_id
        ).select_related("player", "agent")

    def perform_destroy(self, instance):
        logger.info(
            "Agent relationship removed: %s ← %s",
            instance.player.full_name,
            instance.agent.name,
        )
        instance.delete()
