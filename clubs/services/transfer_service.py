"""
BOLAYETU — TransferService

Business logic for player transfers including permanent transfers, loans, and free agents.

Key features:
    - Create transfers with type validation
    - Manage approval workflow for permanent transfers
    - Auto-complete free agents and loans
    - Handle loan end dates and auto-return
    - Convert loans to permanent transfers
    - Cancel transfers with audit trail
"""

from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from typing import Optional, Tuple, List
from datetime import timedelta, date

from core.models import Tenant
from players.models import Player, PlayerRegistration
from clubs.models import Club, Transfer
from competitions.models import Competition


class TransferError(Exception):
    """Raised when transfer operation fails."""
    pass


class TransferNotFound(Exception):
    """Raised when transfer not found."""
    pass


class InvalidTransferType(Exception):
    """Raised when transfer type is invalid."""
    pass


class TransferService:
    """
    Handles player transfers: permanent, loans, and free agents.
    """

    # ─── Transfer Creation ─────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def create_transfer(
        *,
        tenant: Tenant,
        player: Player,
        to_club: Club,
        transfer_date: date,
        transfer_type: str = "permanent",
        from_club: Optional[Club] = None,
        fee: Optional[float] = None,
        loan_end_date: Optional[date] = None,
        salary_contribution: bool = False,
        notes: str = "",
        created_by=None,
    ) -> Transfer:
        """
        Create a new transfer.

        Args:
            tenant: Organization
            player: Player being transferred
            to_club: Destination club
            transfer_date: Date transfer becomes effective
            transfer_type: "permanent", "loan", or "free_agent"
            from_club: Source club (optional for free agents)
            fee: Transfer fee
            loan_end_date: When loan ends (required for loans)
            salary_contribution: Whether from_club pays salary during loan
            notes: Additional notes
            created_by: User creating transfer

        Returns:
            Transfer instance

        Raises:
            InvalidTransferType: If transfer_type is invalid
            TransferError: If validation fails
        """
        # Validate transfer type
        if transfer_type not in dict(Transfer.TransferType.choices):
            raise InvalidTransferType(f"Invalid transfer type: {transfer_type}")

        # Validate free agent signing
        if transfer_type == Transfer.TransferType.FREE_AGENT:
            if from_club is not None:
                raise TransferError("Free agent signings cannot have a from_club")
        else:
            # Permanent and loans require from_club
            if from_club is None:
                raise TransferError(f"{transfer_type} transfers require a from_club")

        # Validate loan specifics
        if transfer_type == Transfer.TransferType.LOAN:
            if not loan_end_date:
                raise TransferError("Loans must have a loan_end_date")
            if loan_end_date <= transfer_date:
                raise TransferError("Loan end date must be after transfer date")

        # Prevent self-transfers
        if from_club and from_club.id == to_club.id:
            raise TransferError("Player cannot transfer to the same club")

        # Create transfer
        transfer = Transfer.objects.create(
            tenant=tenant,
            player=player,
            from_club=from_club,
            to_club=to_club,
            transfer_type=transfer_type,
            transfer_date=transfer_date,
            fee=fee,
            loan_end_date=loan_end_date,
            salary_contribution=salary_contribution,
            notes=notes,
        )

        return transfer

    # ─── Transfer Approval Workflow ────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def approve_transfer(
        *,
        tenant: Tenant,
        transfer: Transfer,
        approved_by=None,
    ) -> Transfer:
        """
        Approve a pending transfer.

        Only permanent transfers require approval.
        Free agents and loans auto-complete.

        Args:
            tenant: Organization
            transfer: Transfer to approve
            approved_by: User approving

        Returns:
            Transfer instance
        """
        if transfer.tenant_id != tenant.id:
            raise TransferError("Transfer does not belong to this organization")

        # Only permanent transfers from club to club require approval
        if not transfer.requires_approval:
            raise TransferError(
                f"Transfer type {transfer.get_transfer_type_display()} does not require approval"
            )

        if transfer.status != Transfer.TransferStatus.PENDING:
            raise TransferError(
                f"Cannot approve transfer with status {transfer.get_status_display()}"
            )

        transfer.approve(approved_by)
        return transfer

    @staticmethod
    @transaction.atomic
    def reject_transfer(
        *,
        tenant: Tenant,
        transfer: Transfer,
        rejected_by=None,
        reason: str = "",
    ) -> Transfer:
        """
        Reject a pending transfer.

        Args:
            tenant: Organization
            transfer: Transfer to reject
            rejected_by: User rejecting
            reason: Rejection reason

        Returns:
            Transfer instance
        """
        if transfer.tenant_id != tenant.id:
            raise TransferError("Transfer does not belong to this organization")

        if transfer.status not in [Transfer.TransferStatus.PENDING, Transfer.TransferStatus.APPROVED]:
            raise TransferError(
                f"Cannot reject transfer with status {transfer.get_status_display()}"
            )

        transfer.reject(rejected_by, reason)
        return transfer

    @staticmethod
    @transaction.atomic
    def complete_transfer(
        *,
        tenant: Tenant,
        transfer: Transfer,
        completed_by=None,
    ) -> Tuple[Transfer, PlayerRegistration]:
        """
        Complete a transfer and update player registration.

        Marks transfer as COMPLETED and creates/updates PlayerRegistration.

        Args:
            tenant: Organization
            transfer: Transfer to complete
            completed_by: User completing

        Returns:
            Tuple of (Transfer, PlayerRegistration)
        """
        if transfer.tenant_id != tenant.id:
            raise TransferError("Transfer does not belong to this organization")

        # Check current status
        if transfer.transfer_type == Transfer.TransferType.PERMANENT:
            # Permanent transfers must be approved
            if transfer.status not in [Transfer.TransferStatus.PENDING, Transfer.TransferStatus.APPROVED]:
                raise TransferError(
                    f"Cannot complete transfer with status {transfer.get_status_display()}"
                )
        else:
            # Free agents and loans can be completed from PENDING
            if transfer.status != Transfer.TransferStatus.PENDING:
                raise TransferError(
                    f"Cannot complete transfer with status {transfer.get_status_display()}"
                )

        # Complete the transfer
        transfer.complete(completed_by)

        # Create/update player registration
        registration = TransferService._create_registration_for_transfer(
            tenant=tenant,
            transfer=transfer,
        )

        return transfer, registration

    @staticmethod
    @transaction.atomic
    def cancel_transfer(
        *,
        tenant: Tenant,
        transfer: Transfer,
        reason: str = "",
    ) -> Transfer:
        """
        Cancel a transfer.

        Args:
            tenant: Organization
            transfer: Transfer to cancel
            reason: Cancellation reason

        Returns:
            Transfer instance
        """
        if transfer.tenant_id != tenant.id:
            raise TransferError("Transfer does not belong to this organization")

        if transfer.status in [Transfer.TransferStatus.CANCELLED, Transfer.TransferStatus.RETURNED]:
            raise TransferError(
                f"Cannot cancel transfer with status {transfer.get_status_display()}"
            )

        transfer.cancel(reason)
        return transfer

    # ─── Loan Management ──────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def extend_loan(
        *,
        tenant: Tenant,
        transfer: Transfer,
        new_end_date: date,
        extended_by=None,
    ) -> Transfer:
        """
        Extend a loan's end date.

        Args:
            tenant: Organization
            transfer: Loan transfer
            new_end_date: New loan end date
            extended_by: User extending

        Returns:
            Transfer instance
        """
        if transfer.tenant_id != tenant.id:
            raise TransferError("Transfer does not belong to this organization")

        if not transfer.is_loan:
            raise TransferError("Only loans can be extended")

        if transfer.status != Transfer.TransferStatus.COMPLETED:
            raise TransferError(
                f"Cannot extend loan with status {transfer.get_status_display()}"
            )

        if new_end_date <= transfer.loan_end_date:
            raise TransferError("New end date must be after current end date")

        transfer.loan_end_date = new_end_date
        transfer.save(update_fields=["loan_end_date", "updated_at"])

        return transfer

    @staticmethod
    @transaction.atomic
    def return_loan(
        *,
        tenant: Tenant,
        transfer: Transfer,
        returned_by=None,
    ) -> Tuple[Transfer, PlayerRegistration]:
        """
        Return a loan (player returns to origin club).

        Creates new registration for origin club.

        Args:
            tenant: Organization
            transfer: Loan transfer
            returned_by: User processing return

        Returns:
            Tuple of (Transfer, PlayerRegistration for origin club)
        """
        if transfer.tenant_id != tenant.id:
            raise TransferError("Transfer does not belong to this organization")

        if not transfer.is_loan:
            raise TransferError("Only loans can be returned")

        if transfer.status != Transfer.TransferStatus.COMPLETED:
            raise TransferError(
                f"Cannot return loan with status {transfer.get_status_display()}"
            )

        # Mark loan as returned
        transfer.make_return(returned_by)

        # Create registration for origin club
        origin_registration = PlayerRegistration.objects.create(
            tenant=tenant,
            player=transfer.player,
            club=transfer.from_club,
            status=PlayerRegistration.RegistrationStatus.REGISTERED,
            registration_date=timezone.now().date(),
            notes=f"Returned from loan to {transfer.to_club.name}",
        )

        return transfer, origin_registration

    @staticmethod
    @transaction.atomic
    def make_loan_permanent(
        *,
        tenant: Tenant,
        transfer: Transfer,
        fee: Optional[float] = None,
        made_permanent_by=None,
    ) -> Transfer:
        """
        Convert a loan to a permanent transfer.

        Args:
            tenant: Organization
            transfer: Loan transfer
            fee: Optional fee for permanent conversion
            made_permanent_by: User converting

        Returns:
            Transfer instance
        """
        if transfer.tenant_id != tenant.id:
            raise TransferError("Transfer does not belong to this organization")

        if not transfer.is_loan:
            raise TransferError("Only loans can be made permanent")

        if transfer.status != Transfer.TransferStatus.COMPLETED:
            raise TransferError(
                f"Cannot convert loan with status {transfer.get_status_display()}"
            )

        transfer.make_permanent(made_permanent_by, fee)
        return transfer

    # ─── Helper Methods ───────────────────────────────────────────────────

    @staticmethod
    def _create_registration_for_transfer(
        *,
        tenant: Tenant,
        transfer: Transfer,
    ) -> PlayerRegistration:
        """
        Create player registration for a completed transfer.

        Marks previous registration as transferred.
        Creates new registration with appropriate status.

        Args:
            tenant: Organization
            transfer: Completed transfer

        Returns:
            New PlayerRegistration
        """
        # Mark previous registrations as transferred
        previous_registrations = PlayerRegistration.objects.filter(
            tenant=tenant,
            player=transfer.player,
            club=transfer.from_club,
            status__in=[
                PlayerRegistration.RegistrationStatus.REGISTERED,
                PlayerRegistration.RegistrationStatus.LOANED,
            ],
        )

        for reg in previous_registrations:
            reg.status = PlayerRegistration.RegistrationStatus.TRANSFERRED
            reg.left_date = transfer.transfer_date
            reg.save(update_fields=["status", "left_date", "updated_at"])

        # Create new registration
        status = (
            PlayerRegistration.RegistrationStatus.LOANED
            if transfer.is_loan
            else PlayerRegistration.RegistrationStatus.REGISTERED
        )

        registration = PlayerRegistration.objects.create(
            tenant=tenant,
            player=transfer.player,
            club=transfer.to_club,
            status=status,
            registration_date=transfer.transfer_date,
            notes=f"{'Loan' if transfer.is_loan else 'Transfer'} from {transfer.from_club.name if transfer.from_club else 'Free Agent'}",
        )

        return registration

    @staticmethod
    def get_transfer(*, tenant: Tenant, transfer_id: int) -> Transfer:
        """Get a transfer by ID."""
        try:
            return Transfer.objects.get(id=transfer_id, tenant=tenant)
        except Transfer.DoesNotExist:
            raise TransferNotFound(f"Transfer {transfer_id} not found")

    @staticmethod
    def list_pending_approvals(
        *,
        tenant: Tenant,
        from_club: Optional[Club] = None,
    ) -> List[Transfer]:
        """
        List pending transfers awaiting approval.

        Args:
            tenant: Organization
            from_club: Filter by origin club (optional)

        Returns:
            List of pending transfers
        """
        queryset = Transfer.objects.filter(
            tenant=tenant,
            status=Transfer.TransferStatus.PENDING,
            transfer_type=Transfer.TransferType.PERMANENT,
        )

        if from_club:
            queryset = queryset.filter(from_club=from_club)

        return list(queryset.select_related("player", "from_club", "to_club"))

    @staticmethod
    def list_active_loans(
        *,
        tenant: Tenant,
        club: Optional[Club] = None,
    ) -> List[Transfer]:
        """
        List active loans.

        Args:
            tenant: Organization
            club: Filter by loaning club (optional)

        Returns:
            List of active loan transfers
        """
        queryset = Transfer.objects.filter(
            tenant=tenant,
            transfer_type=Transfer.TransferType.LOAN,
            status=Transfer.TransferStatus.COMPLETED,
        ).select_related("player", "from_club", "to_club")

        if club:
            queryset = queryset.filter(to_club=club)

        # Filter to currently active loans
        today = timezone.now().date()
        active_loans = [t for t in queryset if t.loan_is_active]

        return active_loans

    @staticmethod
    def list_expiring_loans(
        *,
        tenant: Tenant,
        days_until_expiry: int = 30,
    ) -> List[Transfer]:
        """
        List loans expiring soon.

        Args:
            tenant: Organization
            days_until_expiry: Days window for expiry check

        Returns:
            List of loans expiring soon
        """
        today = timezone.now().date()
        cutoff_date = today + timedelta(days=days_until_expiry)

        queryset = Transfer.objects.filter(
            tenant=tenant,
            transfer_type=Transfer.TransferType.LOAN,
            status=Transfer.TransferStatus.COMPLETED,
            loan_end_date__gte=today,
            loan_end_date__lte=cutoff_date,
        ).select_related("player", "from_club", "to_club").order_by("loan_end_date")

        return list(queryset)
