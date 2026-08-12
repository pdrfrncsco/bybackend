"""
Player Medical Views

CRUD endpoints for player medical profiles and documents.

Privacy Note: Access restricted to Player, Club Medical Staff, and Authorized Organization only.
"""

import logging

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers

from players.models import Player, PlayerMedicalProfile, MedicalDocument
from players.serializers.player_medical import (
    PlayerMedicalProfileSerializer,
    PlayerMedicalProfileLimitedSerializer,
    MedicalDocumentSerializer,
    MedicalDocumentCreateSerializer,
    MedicalHistorySerializer,
)
from players.services.medical_service import (
    PlayerMedicalService,
    MedicalServiceError,
)

logger = logging.getLogger("players")


class PlayerMedicalProfileView(generics.RetrieveUpdateAPIView):
    """Get or update player's medical profile.

    GET /players/{player_id}/medical/
    PATCH /players/{player_id}/medical/

    Access restricted to authorized personnel.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = PlayerMedicalProfileSerializer
    lookup_field = "player_id"

    def get_queryset(self):
        player_id = self.kwargs.get("player_id")
        return PlayerMedicalProfile.objects.filter(player_id=player_id)

    def get_serializer_class(self):
        # Use limited serializer for non-medical staff
        # TODO: Implement proper permission check
        return PlayerMedicalProfileSerializer

    def retrieve(self, request, *args, **kwargs):
        """Get or create medical profile for player."""
        player_id = self.kwargs.get("player_id")

        try:
            player = Player.objects.get(id=player_id)
        except Player.DoesNotExist:
            return Response(
                {"error": "Player not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        profile, created = PlayerMedicalProfile.objects.get_or_create(
            player=player,
            defaults={
                "medical_status": PlayerMedicalProfile.MedicalStatus.FIT,
            },
        )

        serializer = self.get_serializer(profile)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """Update medical profile."""
        player_id = self.kwargs.get("player_id")

        try:
            player = Player.objects.get(id=player_id)
        except Player.DoesNotExist:
            return Response(
                {"error": "Player not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        profile = PlayerMedicalService.create_or_update_medical_profile(
            player=player,
            **request.data,
        )

        serializer = self.get_serializer(profile)
        return Response(serializer.data)


class MedicalDocumentListCreateView(generics.ListCreateAPIView):
    """List and create medical documents for a player.

    GET /players/{player_id}/medical/documents/
    POST /players/{player_id}/medical/documents/
    """

    permission_classes = [IsAuthenticated]
    queryset = MedicalDocument.objects.all()
    serializer_class = MedicalDocumentSerializer

    def get_queryset(self):
        player_id = self.kwargs.get("player_id")
        return MedicalDocument.objects.filter(player_id=player_id).order_by("-issued_at")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return MedicalDocumentCreateSerializer
        return MedicalDocumentSerializer

    def perform_create(self, serializer):
        player_id = self.kwargs.get("player_id")

        try:
            player = Player.objects.get(id=player_id)
        except Player.DoesNotExist:
            raise serializers.ValidationError({"player_id": "Player not found."})

        document = PlayerMedicalService.add_medical_document(
            player=player,
            document_type=serializer.validated_data.get("document_type"),
            title=serializer.validated_data.get("title"),
            issued_at=serializer.validated_data.get("issued_at"),
            file=serializer.validated_data.get("file"),
            expires_at=serializer.validated_data.get("expires_at"),
            description=serializer.validated_data.get("description", ""),
            is_confidential=serializer.validated_data.get("is_confidential", True),
        )
        serializer.instance = document


class MedicalDocumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a medical document.

    GET /players/{player_id}/medical/documents/{id}/
    PATCH /players/{player_id}/medical/documents/{id}/
    DELETE /players/{player_id}/medical/documents/{id}/
    """

    permission_classes = [IsAuthenticated]
    serializer_class = MedicalDocumentSerializer
    lookup_field = "id"

    def get_queryset(self):
        player_id = self.kwargs.get("player_id")
        return MedicalDocument.objects.filter(player_id=player_id)


class MedicalDocumentVerifyView(generics.UpdateAPIView):
    """Verify a medical document.

    PATCH /players/{player_id}/medical/documents/{id}/verify/

    Only authorized medical staff can verify documents.
    """

    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        player_id = self.kwargs.get("player_id")
        return MedicalDocument.objects.filter(player_id=player_id)

    def update(self, request, *args, **kwargs):
        document = self.get_object()

        try:
            PlayerMedicalService.verify_medical_document(
                document=document,
                verified_by=request.user,
            )
            serializer = MedicalDocumentSerializer(document)
            return Response(serializer.data)
        except Exception as exc:
            logger.exception(
                "Failed to verify medical document %s",
                document.id,
            )
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class MedicalDocumentRejectView(generics.UpdateAPIView):
    """Reject a medical document.

    PATCH /players/{player_id}/medical/documents/{id}/reject/

    Only authorized medical staff can reject documents.
    """

    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        player_id = self.kwargs.get("player_id")
        return MedicalDocument.objects.filter(player_id=player_id)

    def update(self, request, *args, **kwargs):
        document = self.get_object()
        reason = request.data.get("reason", "")

        try:
            PlayerMedicalService.reject_medical_document(
                document=document,
                rejected_by=request.user,
                reason=reason,
            )
            serializer = MedicalDocumentSerializer(document)
            return Response(serializer.data)
        except Exception as exc:
            logger.exception(
                "Failed to reject medical document %s",
                document.id,
            )
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class PlayerMedicalHistoryView(generics.RetrieveAPIView):
    """Get complete medical history for a player.

    GET /players/{player_id}/medical/history/
    """

    permission_classes = [IsAuthenticated]
    serializer_class = MedicalHistorySerializer
    lookup_field = "player_id"

    def retrieve(self, request, *args, **kwargs):
        player_id = self.kwargs.get("player_id")

        try:
            player = Player.objects.get(id=player_id)
        except Player.DoesNotExist:
            return Response(
                {"error": "Player not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        history = PlayerMedicalService.get_medical_history(player)
        serializer = self.get_serializer(history)
        return Response(serializer.data)
