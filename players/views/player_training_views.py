"""
Player Training History Views

CRUD endpoints for player training/development history.
"""

import logging

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers

from players.models import Player, PlayerTrainingHistory
from players.serializers.player_training import (
    PlayerTrainingHistorySerializer,
    PlayerTrainingHistoryListSerializer,
    PlayerTrainingHistoryCreateUpdateSerializer,
    TrainingCompensationDataSerializer,
)
from players.services.training_service import (
    PlayerTrainingHistoryService,
    TrainingHistoryError,
)

logger = logging.getLogger("players")


class PlayerTrainingHistoryListCreateView(generics.ListCreateAPIView):
    """List and create player training history entries.

    GET /players/{player_id}/training-history/ — List training history
    POST /players/{player_id}/training-history/ — Add training entry
    """

    permission_classes = [IsAuthenticated]
    queryset = PlayerTrainingHistory.objects.all()
    serializer_class = PlayerTrainingHistorySerializer

    def get_queryset(self):
        player_id = self.kwargs.get("player_id")
        if player_id:
            return PlayerTrainingHistory.objects.filter(
                player_id=player_id
            ).select_related("club").order_by("-start_date")
        return PlayerTrainingHistory.objects.none()

    def get_serializer_class(self):
        if self.request.method == "GET":
            return PlayerTrainingHistoryListSerializer
        return PlayerTrainingHistoryCreateUpdateSerializer

    def perform_create(self, serializer):
        player_id = self.kwargs.get("player_id")
        try:
            player = Player.objects.get(id=player_id)

            entry = PlayerTrainingHistoryService.add_training_entry(
                player=player,
                start_date=serializer.validated_data["start_date"],
                country=serializer.validated_data["country"],
                training_category=serializer.validated_data.get(
                    "training_category",
                    PlayerTrainingHistory.TrainingCategory.AMATEUR,
                ),
                club=serializer.validated_data.get("club"),
                academy_name=serializer.validated_data.get("academy_name", ""),
                end_date=serializer.validated_data.get("end_date"),
                training_certificate=serializer.validated_data.get("training_certificate"),
                notes=serializer.validated_data.get("notes", ""),
            )
            serializer.instance = entry
        except Player.DoesNotExist:
            raise serializers.ValidationError({"player_id": "Player not found."})
        except TrainingHistoryError as exc:
            raise serializers.ValidationError({"training_history": str(exc)})


class PlayerTrainingHistoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a training history entry.

    GET /players/{player_id}/training-history/{entry_id}/ — Get entry
    PATCH /players/{player_id}/training-history/{entry_id}/ — Update entry
    DELETE /players/{player_id}/training-history/{entry_id}/ — Delete entry
    """

    permission_classes = [IsAuthenticated]
    serializer_class = PlayerTrainingHistorySerializer
    lookup_field = "id"

    def get_queryset(self):
        player_id = self.kwargs.get("player_id")
        return PlayerTrainingHistory.objects.filter(
            player_id=player_id
        ).select_related("club", "player")

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return PlayerTrainingHistoryCreateUpdateSerializer
        return PlayerTrainingHistorySerializer


class PlayerTrainingHistoryVerifyView(generics.UpdateAPIView):
    """Verify a training history entry.

    PATCH /players/{player_id}/training-history/{entry_id}/verify/ — Verify entry

    Only admins or authorized staff can verify training history.
    """

    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        player_id = self.kwargs.get("player_id")
        return PlayerTrainingHistory.objects.filter(player_id=player_id)

    def update(self, request, *args, **kwargs):
        entry = self.get_object()

        try:
            PlayerTrainingHistoryService.verify_training_entry(
                entry=entry,
                verified_by=request.user,
            )
            serializer = PlayerTrainingHistorySerializer(entry)
            return Response(serializer.data)
        except Exception as exc:
            logger.exception(
                "Failed to verify training history %s: %s",
                entry.id,
                exc,
            )
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class PlayerTrainingCompensationDataView(generics.RetrieveAPIView):
    """Get training compensation calculation data for a player.

    GET /players/{player_id}/training-compensation/ — Get training data

    Returns:
        {
            "total_years": float,
            "clubs": [
                {
                    "club_id": str,
                    "club_name": str,
                    "years": float,
                    "category": str,
                    "country": str,
                    "verified": bool,
                },
                ...
            ]
        }
    """

    permission_classes = [IsAuthenticated]
    serializer_class = TrainingCompensationDataSerializer
    lookup_field = "player_id"

    def get(self, request, *args, **kwargs):
        player_id = self.kwargs.get("player_id")

        try:
            player = Player.objects.get(id=player_id)
        except Player.DoesNotExist:
            return Response(
                {"error": "Player not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        data = PlayerTrainingHistoryService.get_training_compensation_data(player)
        serializer = TrainingCompensationDataSerializer(data)
        return Response(serializer.data)
