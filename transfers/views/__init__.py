"""
BOLAYETU — Transfer Views

API endpoints for transfers.

Endpoints:
    GET    /api/v1/transfers/                      — List transfers (filterable)
    POST   /api/v1/transfers/                      — Create transfer request
    GET    /api/v1/transfers/{id}/                 — Get transfer detail
    POST   /api/v1/transfers/{id}/approve/         — Approve transfer
    POST   /api/v1/transfers/{id}/reject/          — Reject transfer
    POST   /api/v1/transfers/{id}/complete/        — Complete transfer
    POST   /api/v1/transfers/{id}/cancel/          — Cancel transfer
"""

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from common.responses import success_response, error_response
from common.pagination import StandardPagination
from transfers.models import Transfer
from transfers.selectors import TransferSelector
from transfers.serializers import (
    TransferSerializer,
    TransferDetailSerializer,
    TransferCreateSerializer,
    TransferApprovalSerializer,
    TransferRejectionSerializer,
)
from transfers.services import (
    TransferService,
    TransferNotFound,
    TransferAlreadyProcessed,
    TransferNotApproved,
    TransferInvalidState,
)
from transfers.permissions import (
    CanCreateTransfer,
    CanApproveRejectTransfer,
    CanViewTransfer,
    CanManageTransfers,
)


class TransferListCreateView(APIView):
    """
    GET:  List transfers (filterable by status, player, club).
    POST: Create a new transfer request.
    """

    permission_classes = [IsAuthenticated, CanManageTransfers]

    @extend_schema(
        tags=["transfers"],
        summary="List transfers",
        parameters=[
            OpenApiParameter("status", OpenApiTypes.STR, description="Filter by status (pending, approved, rejected, completed)"),
            OpenApiParameter("player_id", OpenApiTypes.UUID, description="Filter by player ID"),
            OpenApiParameter("from_club_id", OpenApiTypes.UUID, description="Filter by origin club ID"),
            OpenApiParameter("to_club_id", OpenApiTypes.UUID, description="Filter by destination club ID"),
        ],
        responses={200: TransferSerializer(many=True)},
    )
    def get(self, request):
        status = request.query_params.get("status")
        player_id = request.query_params.get("player_id")
        from_club_id = request.query_params.get("from_club_id")
        to_club_id = request.query_params.get("to_club_id")

        if status:
            queryset = TransferSelector.list_by_status(status)
        elif player_id:
            queryset = TransferSelector.list_by_player(player_id)
        elif from_club_id:
            queryset = TransferSelector.list_outgoing_transfers(from_club_id)
        elif to_club_id:
            queryset = TransferSelector.list_incoming_transfers(to_club_id)
        else:
            queryset = TransferSelector.list_all()

        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = TransferSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        tags=["transfers"],
        summary="Create a transfer request",
        request=TransferCreateSerializer,
        responses={201: TransferDetailSerializer},
    )
    def post(self, request):
        serializer = TransferCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from players.models import Player
        from clubs.models import Club
        from competitions.models import Competition

        # Validate player
        player_id = serializer.validated_data.get("player_id")
        try:
            player = Player.objects.get(id=player_id)
        except Player.DoesNotExist:
            return error_response(message="Player not found.", status_code=404)

        # Validate destination club
        to_club_id = serializer.validated_data.get("to_club_id")
        try:
            to_club = Club.objects.get(id=to_club_id)
        except Club.DoesNotExist:
            return error_response(message="Destination club not found.", status_code=404)

        # Validate origin club (if provided)
        from_club = None
        from_club_id = serializer.validated_data.get("from_club_id")
        if from_club_id:
            try:
                from_club = Club.objects.get(id=from_club_id)
            except Club.DoesNotExist:
                return error_response(message="Origin club not found.", status_code=404)

        # Validate competition (if provided)
        competition = None
        competition_id = serializer.validated_data.get("competition_id")
        if competition_id:
            try:
                competition = Competition.objects.get(id=competition_id)
            except Competition.DoesNotExist:
                return error_response(message="Competition not found.", status_code=404)

        try:
            transfer = TransferService.create_transfer(
                player=player,
                to_club=to_club,
                to_tenant=to_club.tenant,
                joined_date=serializer.validated_data.get("joined_date"),
                from_club=from_club,
                from_tenant=from_club.tenant if from_club else None,
                competition=competition,
                shirt_number=serializer.validated_data.get("shirt_number"),
                fee=serializer.validated_data.get("fee"),
            )
        except TransferInvalidState as exc:
            return error_response(message=str(exc), status_code=400)
        except Exception as exc:
            return error_response(message=str(exc), status_code=400)

        result_serializer = TransferDetailSerializer(transfer)
        return success_response(
            data=result_serializer.data,
            message="Transfer request created successfully.",
            status_code=201,
        )


class TransferDetailView(APIView):
    """
    GET: Get transfer detail.
    """

    permission_classes = [IsAuthenticated, CanViewTransfer]

    @extend_schema(
        tags=["transfers"],
        summary="Get transfer detail",
        responses={200: TransferDetailSerializer},
    )
    def get(self, request, transfer_id):
        transfer = TransferSelector.get_by_id(transfer_id)

        if not transfer:
            return error_response(message="Transfer not found.", status_code=404)

        self.check_object_permissions(request, transfer)

        serializer = TransferDetailSerializer(transfer)
        return success_response(data=serializer.data, message="Transfer retrieved successfully.")


class TransferApproveView(APIView):
    """
    POST: Approve a pending transfer.
    Only the origin club can approve.
    """

    permission_classes = [IsAuthenticated, CanApproveRejectTransfer]

    @extend_schema(
        tags=["transfers"],
        summary="Approve a transfer",
        request=TransferApprovalSerializer,
        responses={200: TransferDetailSerializer},
    )
    def post(self, request, transfer_id):
        transfer = TransferSelector.get_by_id(transfer_id)

        if not transfer:
            return error_response(message="Transfer not found.", status_code=404)

        self.check_object_permissions(request, transfer)

        try:
            transfer = TransferService.approve_transfer(transfer)
        except TransferAlreadyProcessed as exc:
            return error_response(message=str(exc), status_code=400)

        serializer = TransferDetailSerializer(transfer)
        return success_response(data=serializer.data, message="Transfer approved successfully.")


class TransferRejectView(APIView):
    """
    POST: Reject a pending transfer.
    Only the origin club can reject.
    """

    permission_classes = [IsAuthenticated, CanApproveRejectTransfer]

    @extend_schema(
        tags=["transfers"],
        summary="Reject a transfer",
        request=TransferRejectionSerializer,
        responses={200: TransferDetailSerializer},
    )
    def post(self, request, transfer_id):
        transfer = TransferSelector.get_by_id(transfer_id)

        if not transfer:
            return error_response(message="Transfer not found.", status_code=404)

        self.check_object_permissions(request, transfer)

        serializer = TransferRejectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        rejection_reason = serializer.validated_data.get("rejection_reason")

        try:
            transfer = TransferService.reject_transfer(transfer, rejection_reason)
        except TransferAlreadyProcessed as exc:
            return error_response(message=str(exc), status_code=400)

        result_serializer = TransferDetailSerializer(transfer)
        return success_response(data=result_serializer.data, message="Transfer rejected.")


class TransferCompleteView(APIView):
    """
    POST: Complete an approved transfer.

    This finalizes the transfer:
    - Deactivates old registration (if any)
    - Creates new registration at destination club
    """

    permission_classes = [IsAuthenticated, CanManageTransfers]

    @extend_schema(
        tags=["transfers"],
        summary="Complete a transfer",
        responses={200: TransferDetailSerializer},
    )
    def post(self, request, transfer_id):
        transfer = TransferSelector.get_by_id(transfer_id)

        if not transfer:
            return error_response(message="Transfer not found.", status_code=404)

        try:
            transfer = TransferService.complete_transfer(transfer)
        except TransferNotApproved as exc:
            return error_response(message=str(exc), status_code=400)
        except Exception as exc:
            return error_response(message=str(exc), status_code=400)

        serializer = TransferDetailSerializer(transfer)
        return success_response(data=serializer.data, message="Transfer completed successfully.")


class TransferCancelView(APIView):
    """
    POST: Cancel a pending transfer.

    Typically called by the requesting club (destination).
    """

    permission_classes = [IsAuthenticated, CanManageTransfers]

    @extend_schema(
        tags=["transfers"],
        summary="Cancel a transfer",
        responses={200: TransferDetailSerializer},
    )
    def post(self, request, transfer_id):
        transfer = TransferSelector.get_by_id(transfer_id)

        if not transfer:
            return error_response(message="Transfer not found.", status_code=404)

        try:
            transfer = TransferService.cancel_transfer(transfer)
        except TransferAlreadyProcessed as exc:
            return error_response(message=str(exc), status_code=400)

        serializer = TransferDetailSerializer(transfer)
        return success_response(data=serializer.data, message="Transfer cancelled.")
