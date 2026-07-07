"""
BOLAYETU — Transfer Services

Write operations for the Transfers domain.

Architecture (01_CODING_STANDARDS.md):
    - Services handle all business logic and mutations.
    - Never call Services from other Services; compose at the view level.
    - Use Selectors for all reads.
"""

import logging
from datetime import date
from typing import Optional

from django.db import transaction
from django.utils import timezone

from transfers.models import Transfer
from players.models import PlayerRegistration

logger = logging.getLogger("transfers")


class TransferNotFound(Exception):
    """Raised when a transfer cannot be found."""
    pass


class TransferAlreadyProcessed(Exception):
    """Raised when trying to modify a transfer that is already completed/rejected."""
    pass


class TransferNotApproved(Exception):
    """Raised when trying to complete a transfer that is not approved."""
    pass


class TransferInvalidState(Exception):
    """Raised when a transfer operation is invalid for the current state."""
    pass


class TransferService:
    """
    Write operations for the Transfer domain.

    Transfers follow a workflow:
        - PENDING: Request created by target club.
        - APPROVED: Approved by origin club (required only if from_club is set).
        - REJECTED: Rejected by origin club.
        - COMPLETED: Old registration deactivated, new registration activated.
    """

    @staticmethod
    @transaction.atomic
    def create_transfer(
        player,
        to_club,
        to_tenant,
        joined_date: date,
        from_club=None,
        from_tenant=None,
        competition=None,
        shirt_number: Optional[int] = None,
        fee: Optional[float] = None,
    ) -> Transfer:
        """
        Create a new transfer request.

        If from_club is None, this is a "Free Agent to Club" transfer
        and goes directly to COMPLETED status.

        If from_club is set, the transfer starts as PENDING and requires
        approval from the origin club.
        """
        # Validate: player must have an active registration at from_club (if set)
        if from_club:
            active_registration = PlayerRegistration.objects.filter(
                player=player,
                club=from_club,
                status__in=["registered", "loaned"],
            ).first()

            if not active_registration:
                raise TransferInvalidState(
                    f"Player {player.full_name} does not have an active registration at {from_club.name}."
                )

        # Determine initial status
        if from_club is None:
            # Free agent transfer - auto-complete
            status = Transfer.TransferStatus.COMPLETED
            completed_date = timezone.now()
        else:
            # Club-to-club transfer - requires approval
            status = Transfer.TransferStatus.PENDING
            completed_date = None

        transfer = Transfer.objects.create(
            player=player,
            from_club=from_club,
            to_club=to_club,
            from_tenant=from_tenant,
            to_tenant=to_tenant,
            competition=competition,
            joined_date=joined_date,
            shirt_number=shirt_number,
            fee=fee,
            status=status,
            completed_date=completed_date,
        )

        # If free agent transfer, create the registration immediately
        if from_club is None:
            PlayerRegistration.objects.create(
                player=player,
                club=to_club,
                tenant=to_tenant,
                competition=competition,
                joined_date=joined_date,
                shirt_number=shirt_number,
                status=PlayerRegistration.RegistrationStatus.REGISTERED,
            )
            logger.info(
                "Free agent transfer completed: %s → %s (id=%s)",
                player.full_name, to_club.name, transfer.id
            )
        else:
            logger.info(
                "Transfer request created: %s from %s → %s (id=%s, status=%s)",
                player.full_name, from_club.name, to_club.name, transfer.id, status
            )

        return transfer

    @staticmethod
    @transaction.atomic
    def approve_transfer(transfer: Transfer) -> Transfer:
        """
        Approve a pending transfer.

        Only the origin club can approve.
        Transitions: PENDING → APPROVED
        """
        if transfer.status != Transfer.TransferStatus.PENDING:
            raise TransferAlreadyProcessed(
                f"Transfer is already {transfer.status}. Only PENDING transfers can be approved."
            )

        transfer.status = Transfer.TransferStatus.APPROVED
        transfer.save(update_fields=["status"])

        logger.info(
            "Transfer approved: %s from %s → %s (id=%s)",
            transfer.player.full_name,
            transfer.from_club.name if transfer.from_club else "Free Agent",
            transfer.to_club.name,
            transfer.id
        )
        return transfer

    @staticmethod
    @transaction.atomic
    def reject_transfer(transfer: Transfer, rejection_reason: Optional[str] = None) -> Transfer:
        """
        Reject a pending transfer.

        Only the origin club can reject.
        Transitions: PENDING → REJECTED
        """
        if transfer.status != Transfer.TransferStatus.PENDING:
            raise TransferAlreadyProcessed(
                f"Transfer is already {transfer.status}. Only PENDING transfers can be rejected."
            )

        transfer.status = Transfer.TransferStatus.REJECTED
        transfer.rejection_reason = rejection_reason
        transfer.save(update_fields=["status", "rejection_reason"])

        logger.info(
            "Transfer rejected: %s from %s → %s (id=%s, reason=%s)",
            transfer.player.full_name,
            transfer.from_club.name if transfer.from_club else "Free Agent",
            transfer.to_club.name,
            transfer.id,
            rejection_reason or "No reason provided"
        )
        return transfer

    @staticmethod
    @transaction.atomic
    def complete_transfer(transfer: Transfer) -> Transfer:
        """
        Complete an approved transfer.

        - Deactivates the player's old registration at from_club
        - Creates a new registration at to_club
        - Transitions: APPROVED → COMPLETED

        For free agent transfers (no from_club), PENDING is allowed since no approval is needed.
        """
        # PENDING is allowed for free agent transfers (no from_club)
        # Otherwise, transfer must be APPROVED
        if transfer.from_club:
            if transfer.status != Transfer.TransferStatus.APPROVED:
                raise TransferNotApproved(
                    f"Transfer must be APPROVED before completion. Current status: {transfer.status}"
                )
        else:
            # Free agent transfer - must be PENDING or APPROVED
            if transfer.status not in [Transfer.TransferStatus.APPROVED, Transfer.TransferStatus.PENDING]:
                raise TransferNotApproved(
                    f"Transfer must be APPROVED or PENDING before completion. Current status: {transfer.status}"
                )

        # If there's an origin club, deactivate the old registration
        if transfer.from_club:
            old_registration = PlayerRegistration.objects.filter(
                player=transfer.player,
                club=transfer.from_club,
                status__in=["registered", "loaned"],
            ).first()

            if old_registration:
                old_registration.deactivate(left_date=transfer.joined_date)

        # Create new registration at destination club
        PlayerRegistration.objects.create(
            player=transfer.player,
            club=transfer.to_club,
            tenant=transfer.to_tenant,
            competition=transfer.competition,
            joined_date=transfer.joined_date,
            shirt_number=transfer.shirt_number,
            status=PlayerRegistration.RegistrationStatus.REGISTERED,
        )

        transfer.status = Transfer.TransferStatus.COMPLETED
        transfer.completed_date = timezone.now()
        transfer.save(update_fields=["status", "completed_date"])

        logger.info(
            "Transfer completed: %s %s → %s (id=%s)",
            transfer.player.full_name,
            f"from {transfer.from_club.name}" if transfer.from_club else "(free agent)",
            transfer.to_club.name,
            transfer.id
        )
        return transfer

    @staticmethod
    @transaction.atomic
    def cancel_transfer(transfer: Transfer) -> Transfer:
        """
        Cancel a pending transfer.

        Can only cancel PENDING transfers.
        Typically called by the requesting club (to_club).
        """
        if transfer.status != Transfer.TransferStatus.PENDING:
            raise TransferAlreadyProcessed(
                f"Transfer is already {transfer.status}. Only PENDING transfers can be cancelled."
            )

        transfer.status = Transfer.TransferStatus.REJECTED
        transfer.rejection_reason = "Cancelled by requesting club."
        transfer.save(update_fields=["status", "rejection_reason"])

        logger.info(
            "Transfer cancelled: %s from %s → %s (id=%s)",
            transfer.player.full_name,
            transfer.from_club.name if transfer.from_club else "Free Agent",
            transfer.to_club.name,
            transfer.id
        )
        return transfer
