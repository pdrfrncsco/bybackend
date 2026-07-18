"""
BOLAYETU — Transfer Views

REST API endpoints for player transfers, loans, and free agent signings.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from common.pagination import StandardPagination
from accounts.models import TenantMembership
from accounts.selectors import TenantMembershipSelector
from clubs.models import Club, Transfer
from clubs.serializers.transfer_serializers import (
    TransferSerializer, TransferCreateSerializer,
    TransferApproveSerializer, TransferRejectSerializer,
    TransferCancelSerializer, LoanExtendSerializer,
    LoanReturnSerializer, LoanMakePermanentSerializer,
    TransferListSerializer,
)
from clubs.services.transfer_service import (
    TransferService, TransferError, InvalidTransferType,
    TransferNotFound,
)
from players.models import Player


class TransferViewSet(viewsets.ModelViewSet):
    """
    API endpoints for player transfers.

    - POST /clubs/transfers/
        Create new transfer (permanent, loan, free agent)
    - GET /clubs/transfers/
        List transfers
    - GET /clubs/transfers/{id}/
        Get transfer details
    - POST /clubs/transfers/{id}/approve/
        Approve pending transfer
    - POST /clubs/transfers/{id}/reject/
        Reject pending transfer
    - POST /clubs/transfers/{id}/complete/
        Complete transfer
    - POST /clubs/transfers/{id}/cancel/
        Cancel transfer
    - POST /clubs/transfers/{id}/extend-loan/
        Extend loan duration
    - POST /clubs/transfers/{id}/return-loan/
        Return loan to origin club
    - POST /clubs/transfers/{id}/make-permanent/
        Convert loan to permanent
    """

    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    queryset = Transfer.objects.all()

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return TransferCreateSerializer
        elif self.action == 'list':
            return TransferListSerializer
        elif self.action == 'approve':
            return TransferApproveSerializer
        elif self.action == 'reject':
            return TransferRejectSerializer
        elif self.action == 'cancel':
            return TransferCancelSerializer
        elif self.action == 'extend_loan':
            return LoanExtendSerializer
        elif self.action == 'return_loan':
            return LoanReturnSerializer
        elif self.action == 'make_permanent':
            return LoanMakePermanentSerializer
        return TransferSerializer

    def _get_tenant(self):
        """
        Resolve the tenant for the current request.

        Prefer the tenant resolved by middleware when available. Fall back to
        a user-attached tenant for legacy test fixtures, then to the first
        active membership.
        """
        request_tenant = getattr(self.request, "tenant", None)
        if request_tenant is not None:
            membership = TenantMembershipSelector.get_membership(
                user=self.request.user,
                tenant_id=request_tenant.id,
            )
            if membership and membership.is_active:
                return request_tenant
            raise PermissionDenied("You do not have access to this tenant.")

        legacy_tenant = getattr(self.request.user, "tenant", None)
        if legacy_tenant is not None:
            return legacy_tenant

        membership = (
            TenantMembership.objects
            .filter(user=self.request.user, is_active=True)
            .select_related("tenant")
            .first()
        )
        if membership:
            return membership.tenant

        raise PermissionDenied("Unable to resolve tenant for the authenticated user.")

    def get_queryset(self):
        """Filter transfers by tenant."""
        tenant = self._get_tenant()
        return Transfer.objects.filter(
            tenant=tenant
        ).select_related('player', 'from_club', 'to_club')

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Create a new transfer."""
        tenant = self._get_tenant()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            player = Player.objects.get(
                id=serializer.validated_data['player_id']
            )
            to_club = Club.objects.get(
                id=serializer.validated_data['to_club_id'],
                tenant=tenant
            )
            from_club = None
            if serializer.validated_data.get('from_club_id'):
                from_club = Club.objects.get(
                    id=serializer.validated_data['from_club_id'],
                    tenant=tenant
                )

            transfer = TransferService.create_transfer(
                tenant=tenant,
                player=player,
                to_club=to_club,
                transfer_date=serializer.validated_data['transfer_date'],
                transfer_type=serializer.validated_data.get('transfer_type', 'permanent'),
                from_club=from_club,
                fee=serializer.validated_data.get('fee'),
                loan_end_date=serializer.validated_data.get('loan_end_date'),
                salary_contribution=serializer.validated_data.get('salary_contribution', False),
                notes=serializer.validated_data.get('notes', ''),
                created_by=request.user,
            )

            response_serializer = TransferSerializer(transfer)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        except (Player.DoesNotExist, Club.DoesNotExist):
            return Response(
                {"error": "Player or club not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except InvalidTransferType as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except TransferError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def approve(self, request, pk=None):
        """Approve a pending transfer."""
        tenant = self._get_tenant()
        transfer = self.get_object()

        try:
            transfer = TransferService.approve_transfer(
                tenant=tenant,
                transfer=transfer,
                approved_by=request.user,
            )

            serializer = TransferSerializer(transfer)
            return Response(serializer.data)

        except TransferError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def reject(self, request, pk=None):
        """Reject a pending transfer."""
        tenant = self._get_tenant()
        transfer = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            transfer = TransferService.reject_transfer(
                tenant=tenant,
                transfer=transfer,
                rejected_by=request.user,
                reason=serializer.validated_data.get('reason', ''),
            )

            response_serializer = TransferSerializer(transfer)
            return Response(response_serializer.data)

        except TransferError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def complete(self, request, pk=None):
        """Complete a transfer and create player registration."""
        tenant = self._get_tenant()
        transfer = self.get_object()

        try:
            transfer, registration = TransferService.complete_transfer(
                tenant=tenant,
                transfer=transfer,
                completed_by=request.user,
            )

            serializer = TransferSerializer(transfer)
            return Response({
                "transfer": serializer.data,
                "registration": {
                    "id": str(registration.id),
                    "player": registration.player.full_name,
                    "club": registration.club.name,
                    "status": registration.status,
                    "registration_date": registration.registration_date,
                }
            })

        except TransferError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def cancel(self, request, pk=None):
        """Cancel a transfer."""
        tenant = self._get_tenant()
        transfer = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            transfer = TransferService.cancel_transfer(
                tenant=tenant,
                transfer=transfer,
                reason=serializer.validated_data.get('reason', ''),
            )

            response_serializer = TransferSerializer(transfer)
            return Response(response_serializer.data)

        except TransferError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    # ─── Loan Specific Actions ──────────────────────────────────────────────

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def extend_loan(self, request, pk=None):
        """Extend a loan's end date."""
        tenant = self._get_tenant()
        transfer = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            transfer = TransferService.extend_loan(
                tenant=tenant,
                transfer=transfer,
                new_end_date=serializer.validated_data['new_end_date'],
                extended_by=request.user,
            )

            response_serializer = TransferSerializer(transfer)
            return Response(response_serializer.data)

        except TransferError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def return_loan(self, request, pk=None):
        """Return a loan to the origin club."""
        tenant = self._get_tenant()
        transfer = self.get_object()

        try:
            transfer, registration = TransferService.return_loan(
                tenant=tenant,
                transfer=transfer,
                returned_by=request.user,
            )

            serializer = TransferSerializer(transfer)
            return Response({
                "transfer": serializer.data,
                "registration": {
                    "id": str(registration.id),
                    "player": registration.player.full_name,
                    "club": registration.club.name,
                    "status": registration.status,
                    "registration_date": registration.registration_date,
                }
            })

        except TransferError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def make_permanent(self, request, pk=None):
        """Convert a loan to a permanent transfer."""
        tenant = self._get_tenant()
        transfer = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            transfer = TransferService.make_loan_permanent(
                tenant=tenant,
                transfer=transfer,
                fee=serializer.validated_data.get('fee'),
                made_permanent_by=request.user,
            )

            response_serializer = TransferSerializer(transfer)
            return Response(response_serializer.data)

        except TransferError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    # ─── List Actions ───────────────────────────────────────────────────────

    @action(detail=False, methods=['get'])
    def pending_approvals(self, request):
        """List pending transfers awaiting approval."""
        tenant = self._get_tenant()
        club_id = request.query_params.get('club_id')

        club = None
        if club_id:
            club = get_object_or_404(Club, id=club_id, tenant=tenant)

        transfers = TransferService.list_pending_approvals(
            tenant=tenant,
            from_club=club,
        )

        serializer = self.get_serializer(transfers, many=True)
        return Response({"results": serializer.data})

    @action(detail=False, methods=['get'])
    def active_loans(self, request):
        """List active loans."""
        tenant = self._get_tenant()
        club_id = request.query_params.get('club_id')

        club = None
        if club_id:
            club = get_object_or_404(Club, id=club_id, tenant=tenant)

        transfers = TransferService.list_active_loans(
            tenant=tenant,
            club=club,
        )

        serializer = TransferListSerializer(transfers, many=True)
        return Response({"results": serializer.data})

    @action(detail=False, methods=['get'])
    def expiring_loans(self, request):
        """List loans expiring soon."""
        tenant = self._get_tenant()
        days = request.query_params.get('days', 30)

        try:
            days = int(days)
        except (ValueError, TypeError):
            days = 30

        transfers = TransferService.list_expiring_loans(
            tenant=tenant,
            days_until_expiry=days,
        )

        serializer = TransferListSerializer(transfers, many=True)
        return Response({"results": serializer.data})
