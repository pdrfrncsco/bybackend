"""
Player Contract Views

CRUD endpoints for player contracts.
"""

import logging
from datetime import date

from rest_framework import generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers

from players.models import Player, PlayerContract
from players.serializers.player_contract import (
    PlayerContractSerializer,
    PlayerContractListSerializer,
    PlayerContractCreateUpdateSerializer,
)
from players.services.contract_service import PlayerContractService, PlayerContractError

logger = logging.getLogger("players")


class PlayerContractListCreateView(generics.ListCreateAPIView):
    """List and create player contracts.
    
    GET /players/{player_id}/contracts/ — List contracts for a player
    POST /players/{player_id}/contracts/ — Create a new contract
    """
    
    permission_classes = [IsAuthenticated]
    queryset = PlayerContract.objects.all()
    serializer_class = PlayerContractSerializer

    def get_queryset(self):
        player_id = self.kwargs.get("player_id")
        if player_id:
            return PlayerContract.objects.filter(player_id=player_id).select_related(
                "player", "club", "tenant"
            ).order_by("-start_date")
        return PlayerContract.objects.none()

    def get_serializer_class(self):
        if self.request.method == "GET":
            return PlayerContractListSerializer
        return PlayerContractCreateUpdateSerializer

    def perform_create(self, serializer):
        try:
            player_id = self.kwargs.get("player_id")
            player = Player.objects.get(id=player_id)
            
            contract = PlayerContractService.create_contract(
                player=player,
                club=serializer.validated_data["club"],
                contract_type=serializer.validated_data.get(
                    "contract_type", PlayerContract.ContractType.PROFESSIONAL
                ),
                start_date=serializer.validated_data["start_date"],
                end_date=serializer.validated_data["end_date"],
                tenant=serializer.validated_data["tenant"],
                salary=serializer.validated_data.get("salary"),
                currency=serializer.validated_data.get("currency", "USD"),
                bonuses=serializer.validated_data.get("bonuses", {}),
                release_clause=serializer.validated_data.get("release_clause"),
                has_image_rights=serializer.validated_data.get("has_image_rights", False),
            )
            serializer.instance = contract
        except Player.DoesNotExist:
            raise serializers.ValidationError({"player_id": "Player not found."})
        except PlayerContractError as exc:
            raise serializers.ValidationError({"contract": str(exc)})


class PlayerContractDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a specific contract.
    
    GET /players/{player_id}/contracts/{contract_id}/ — Get contract
    PATCH /players/{player_id}/contracts/{contract_id}/ — Update contract
    DELETE /players/{player_id}/contracts/{contract_id}/ — Soft delete (mark as terminated)
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = PlayerContractSerializer
    lookup_field = "id"

    def get_queryset(self):
        player_id = self.kwargs.get("player_id")
        return PlayerContract.objects.filter(player_id=player_id).select_related(
            "player", "club", "tenant"
        )

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return PlayerContractCreateUpdateSerializer
        return PlayerContractSerializer

    def perform_destroy(self, instance):
        """Soft delete: mark as terminated instead of deleting."""
        try:
            PlayerContractService.terminate_contract(instance, terminated_reason="Removed by user")
        except Exception as exc:
            logger.exception("Failed to terminate contract %s: %s", instance.id, exc)


class PlayerContractSignView(generics.UpdateAPIView):
    """Sign a contract (player or club signature).
    
    PATCH /players/{player_id}/contracts/{contract_id}/sign/ — Sign contract
    
    Body:
    {
        "signed_by_player": true,
        "signed_by_club": false
    }
    """
    
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        player_id = self.kwargs.get("player_id")
        return PlayerContract.objects.filter(player_id=player_id)

    def update(self, request, *args, **kwargs):
        contract = self.get_object()
        signed_by_player = request.data.get("signed_by_player", False)
        signed_by_club = request.data.get("signed_by_club", False)

        try:
            PlayerContractService.sign_contract(
                contract,
                signed_by_player=signed_by_player,
                signed_by_club=signed_by_club,
            )
            serializer = PlayerContractSerializer(contract)
            return Response(serializer.data)
        except Exception as exc:
            logger.exception("Failed to sign contract %s: %s", contract.id, exc)
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class PlayerContractRenewView(generics.CreateAPIView):
    """Renew an existing contract.
    
    POST /players/{player_id}/contracts/{contract_id}/renew/ — Renew contract
    
    Body:
    {
        "new_end_date": "2027-12-31",
        "renewal_bonuses": {"appearance": 1000}
    }
    """
    
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_contract(self):
        player_id = self.kwargs.get("player_id")
        contract_id = self.kwargs.get("id")
        return PlayerContract.objects.get(id=contract_id, player_id=player_id)

    def create(self, request, *args, **kwargs):
        try:
            contract = self.get_contract()
            new_end_date_str = request.data.get("new_end_date")
            renewal_bonuses = request.data.get("renewal_bonuses")

            if not new_end_date_str:
                return Response(
                    {"error": "new_end_date is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                new_end_date = date.fromisoformat(new_end_date_str)
            except ValueError:
                return Response(
                    {"error": "Invalid date format. Expected YYYY-MM-DD."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            PlayerContractService.renew_contract(
                contract,
                new_end_date=new_end_date,
                renewal_bonuses=renewal_bonuses or {},
            )
            serializer = PlayerContractSerializer(contract)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except PlayerContract.DoesNotExist:
            return Response(
                {"error": "Contract not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as exc:
            logger.exception("Failed to renew contract: %s", exc)
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class PlayerContractTerminateView(generics.UpdateAPIView):
    """Terminate a contract.
    
    PATCH /players/{player_id}/contracts/{contract_id}/terminate/ — Terminate contract
    
    Body:
    {
        "reason": "Mutual agreement"
    }
    """
    
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        player_id = self.kwargs.get("player_id")
        return PlayerContract.objects.filter(player_id=player_id)

    def update(self, request, *args, **kwargs):
        contract = self.get_object()
        reason = request.data.get("reason", "Not specified")

        try:
            PlayerContractService.terminate_contract(contract, terminated_reason=reason)
            serializer = PlayerContractSerializer(contract)
            return Response(serializer.data)
        except Exception as exc:
            logger.exception("Failed to terminate contract %s: %s", contract.id, exc)
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
