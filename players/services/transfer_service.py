"""
PlayerTransferService

Orchestrates player transfers between clubs, integrating:
- PlayerRegistration (closing old, creating new)
- PlayerContract (terminating old, creating new if applicable)
- Transfer record creation (delegated to transfers module)
- Domain events emission

This service lives in players/ because it orchestrates player lifecycle events,
even though it integrates with the transfers module.
"""

import logging
from datetime import date
from typing import Optional

from django.db import transaction

from players.models import Player, PlayerRegistration, PlayerContract
from players.events.types import (
    publish_player_transferred,
    publish_player_released,
    publish_player_loan_started,
    publish_player_loan_ended,
)

logger = logging.getLogger("players")


class PlayerTransferService:
    """Service for orchestrating player transfers.

    This service coordinates:
    1. Closing the current registration (and optionally contract)
    2. Creating the new registration (and optionally contract)
    3. Updating PlayerCareer history
    4. Emitting domain events

    The actual Transfer record is managed by the transfers module.
    """

    @staticmethod
    @transaction.atomic
    def execute_transfer(
        player: Player,
        from_club,
        to_club,
        to_tenant,
        joined_date: date,
        competition=None,
        shirt_number: Optional[int] = None,
        transfer_fee: Optional[float] = None,
        new_contract_data: Optional[dict] = None,
        transfer_record=None,
        approved_by=None,
    ) -> dict:
        """Execute a complete player transfer.

        This is the main entry point for completing a transfer.
        It handles:
        1. Closing the old registration
        2. Creating the new registration
        3. Closing the old contract (if exists)
        4. Creating new contract (if data provided)
        5. Updating career history
        6. Emitting events

        Args:
            player: Player instance
            from_club: Origin club (can be None for free agents)
            to_club: Destination club
            to_tenant: Destination tenant
            joined_date: Date player joins new club
            competition: Optional competition for new registration
            shirt_number: Optional shirt number
            transfer_fee: Optional transfer fee amount
            new_contract_data: Optional dict with contract details
            transfer_record: Optional Transfer instance from transfers module
            approved_by: User who approved the transfer

        Returns:
            {
                "old_registration": PlayerRegistration | None,
                "new_registration": PlayerRegistration,
                "old_contract": PlayerContract | None,
                "new_contract": PlayerContract | None,
            }

        Raises:
            TransferError if validation or execution fails.
        """
        from players.services import PlayerRegistrationService, PlayerRegistrationConflict

        # Step 1: Get and close old registration if exists
        old_registration = None
        if from_club:
            old_registration = PlayerRegistration.objects.filter(
                player=player,
                club=from_club,
                status__in=[
                    PlayerRegistration.RegistrationStatus.REGISTERED,
                    PlayerRegistration.RegistrationStatus.LOANED,
                ],
            ).first()

            if old_registration:
                old_registration.deactivate(left_date=joined_date)
                logger.info(
                    "Closed old registration: %s left %s",
                    player.full_name,
                    from_club.name,
                )

        # Step 2: Create new registration
        try:
            new_registration = PlayerRegistrationService.register_player(
                player=player,
                club=to_club,
                tenant=to_tenant,
                joined_date=joined_date,
                shirt_number=shirt_number,
                competition=competition,
            )
        except PlayerRegistrationConflict as exc:
            raise TransferError(str(exc))

        # Step 3: Handle contracts if applicable
        old_contract = None
        new_contract = None

        if from_club:
            # Get active contract at old club
            old_contract = PlayerContract.objects.filter(
                player=player,
                club=from_club,
                status=PlayerContract.ContractStatus.ACTIVE,
            ).first()

            if old_contract:
                from players.services.contract_service import PlayerContractService
                PlayerContractService.terminate_contract(
                    old_contract,
                    terminated_reason="Transfer to another club",
                )
                logger.info(
                    "Terminated old contract: %s @ %s",
                    player.full_name,
                    from_club.name,
                )

        # Create new contract if data provided
        if new_contract_data:
            from players.services.contract_service import PlayerContractService

            try:
                new_contract = PlayerContractService.create_contract(
                    player=player,
                    club=to_club,
                    tenant=to_tenant,
                    contract_type=new_contract_data.get(
                        "contract_type",
                        PlayerContract.ContractType.PROFESSIONAL,
                    ),
                    start_date=new_contract_data.get("start_date", joined_date),
                    end_date=new_contract_data["end_date"],
                    salary=new_contract_data.get("salary"),
                    currency=new_contract_data.get("currency", "USD"),
                    bonuses=new_contract_data.get("bonuses"),
                    release_clause=new_contract_data.get("release_clause"),
                    has_image_rights=new_contract_data.get("has_image_rights", False),
                )
                logger.info(
                    "Created new contract: %s @ %s",
                    player.full_name,
                    to_club.name,
                )
            except Exception as exc:
                logger.exception(
                    "Failed to create new contract for %s at %s",
                    player.full_name,
                    to_club.name,
                )
                # Don't fail the whole transfer if contract creation fails
                new_contract = None

        # Step 4: Update career history (via PlayerCareer model)
        try:
            PlayerTransferService._update_career_history(
                player=player,
                old_registration=old_registration,
                new_registration=new_registration,
            )
        except Exception:
            logger.exception(
                "Failed to update career history for player %s",
                player.id,
            )

        # Step 5: Emit domain event
        try:
            publish_player_transferred(
                player_id=str(player.id),
                from_club_id=str(from_club.id) if from_club else None,
                to_club_id=str(to_club.id),
                transfer_fee=transfer_fee,
                tenant_id=str(to_tenant.id),
            )
        except Exception:
            logger.exception(
                "Failed to publish PlayerTransferred event for %s",
                player.id,
            )

        logger.info(
            "Transfer completed: %s → %s (fee: %s)",
            player.full_name,
            to_club.name,
            transfer_fee or "N/A",
        )

        return {
            "old_registration": old_registration,
            "new_registration": new_registration,
            "old_contract": old_contract,
            "new_contract": new_contract,
        }

    @staticmethod
    @transaction.atomic
    def release_player(
        player: Player,
        from_club,
        release_date: Optional[date] = None,
        reason: Optional[str] = None,
    ) -> PlayerRegistration:
        """Release a player from a club (becomes free agent).

        Args:
            player: Player instance
            from_club: Club releasing the player
            release_date: Date of release (defaults to today)
            reason: Optional release reason

        Returns:
            The deactivated PlayerRegistration

        Raises:
            TransferError if player has no active registration at the club.
        """
        release_date = release_date or date.today()

        # Get active registration
        registration = PlayerRegistration.objects.filter(
            player=player,
            club=from_club,
            status__in=[
                PlayerRegistration.RegistrationStatus.REGISTERED,
                PlayerRegistration.RegistrationStatus.LOANED,
            ],
        ).first()

        if not registration:
            raise TransferError(
                f"Player {player.full_name} has no active registration at {from_club.name}."
            )

        # Deactivate registration
        registration.deactivate(left_date=release_date)

        # Terminate contract if exists
        contract = PlayerContract.objects.filter(
            player=player,
            club=from_club,
            status=PlayerContract.ContractStatus.ACTIVE,
        ).first()

        if contract:
            from players.services.contract_service import PlayerContractService
            PlayerContractService.terminate_contract(
                contract,
                terminated_reason=reason or "Player released",
            )

        # Emit event
        try:
            publish_player_released(
                player_id=str(player.id),
                from_club_id=str(from_club.id),
                reason=reason or "",
                tenant_id=str(from_club.tenant_id) if from_club.tenant_id else None,
            )
        except Exception:
            logger.exception(
                "Failed to publish PlayerReleased event for %s",
                player.id,
            )

        logger.info(
            "Player released: %s ← %s (reason: %s)",
            player.full_name,
            from_club.name,
            reason or "not specified",
        )

        return registration

    @staticmethod
    @transaction.atomic
    def start_loan(
        player: Player,
        from_club,
        to_club,
        to_tenant,
        loan_start_date: date,
        loan_end_date: date,
        competition=None,
        shirt_number: Optional[int] = None,
    ) -> dict:
        """Start a loan for a player.

        Unlike a transfer, the original registration remains but is marked as LOANED.

        Args:
            player: Player instance
            from_club: Owning club
            to_club: Destination club (loan)
            to_tenant: Destination tenant
            loan_start_date: Start date of loan
            loan_end_date: End date of loan
            competition: Optional competition
            shirt_number: Optional shirt number at loan club

        Returns:
            {
                "original_registration": PlayerRegistration (status=LOANED),
                "loan_registration": PlayerRegistration,
            }
        """
        # Get and mark original registration as LOANED
        original_registration = PlayerRegistration.objects.filter(
            player=player,
            club=from_club,
            status=PlayerRegistration.RegistrationStatus.REGISTERED,
        ).first()

        if not original_registration:
            raise TransferError(
                f"Player {player.full_name} has no active registration at {from_club.name} to loan from."
            )

        original_registration.status = PlayerRegistration.RegistrationStatus.LOANED
        original_registration.save(update_fields=["status"])

        # Create loan registration at destination
        loan_registration = PlayerRegistration.objects.create(
            player=player,
            club=to_club,
            tenant=to_tenant,
            competition=competition,
            joined_date=loan_start_date,
            shirt_number=shirt_number,
            status=PlayerRegistration.RegistrationStatus.LOANED,
        )

        # Create loan contract if needed (optional - clubs may handle separately)
        # For simplicity, we don't auto-create loan contracts here

        # Emit event
        try:
            publish_player_loan_started(
                player_id=str(player.id),
                from_club_id=str(from_club.id),
                to_club_id=str(to_club.id),
                loan_start_date=loan_start_date.isoformat(),
                loan_end_date=loan_end_date.isoformat(),
                tenant_id=str(to_tenant.id),
            )
        except Exception:
            logger.exception(
                "Failed to publish PlayerLoanStarted event for %s",
                player.id,
            )

        logger.info(
            "Loan started: %s → %s (%s to %s)",
            player.full_name,
            to_club.name,
            loan_start_date,
            loan_end_date,
        )

        return {
            "original_registration": original_registration,
            "loan_registration": loan_registration,
        }

    @staticmethod
    @transaction.atomic
    def end_loan(
        player: Player,
        loan_club,
        end_date: Optional[date] = None,
    ) -> PlayerRegistration:
        """End a loan and return player to parent club.

        Args:
            player: Player instance
            loan_club: Club where player is on loan
            end_date: End date (defaults to today)

        Returns:
            The loan registration (deactivated)
        """
        end_date = end_date or date.today()

        # Get loan registration
        loan_registration = PlayerRegistration.objects.filter(
            player=player,
            club=loan_club,
            status=PlayerRegistration.RegistrationStatus.LOANED,
        ).first()

        if not loan_registration:
            raise TransferError(
                f"Player {player.full_name} has no active loan at {loan_club.name}."
            )

        # Deactivate loan registration
        loan_registration.deactivate(left_date=end_date)

        # Restore original registration to REGISTERED
        original_registration = PlayerRegistration.objects.filter(
            player=player,
            status=PlayerRegistration.RegistrationStatus.LOANED,
        ).exclude(club=loan_club).first()

        if original_registration:
            original_registration.status = PlayerRegistration.RegistrationStatus.REGISTERED
            original_registration.save(update_fields=["status"])

        # Emit event
        try:
            publish_player_loan_ended(
                player_id=str(player.id),
                loan_club_id=str(loan_club.id),
                parent_club_id=str(original_registration.club.id) if original_registration else None,
                end_date=end_date.isoformat(),
                tenant_id=str(loan_club.tenant_id) if loan_club.tenant_id else None,
            )
        except Exception:
            logger.exception(
                "Failed to publish PlayerLoanEnded event for %s",
                player.id,
            )

        logger.info(
            "Loan ended: %s returned from %s",
            player.full_name,
            loan_club.name,
        )

        return loan_registration

    @staticmethod
    def _update_career_history(
        player: Player,
        old_registration: Optional[PlayerRegistration],
        new_registration: PlayerRegistration,
    ) -> None:
        """Update PlayerCareer records after transfer.

        This creates or updates PlayerCareer entries for both clubs.
        Note: PlayerCareer doesn't have start_date/end_date fields;
        it uses season-based aggregation instead.
        """
        from players.models import PlayerCareer

        # Create new career entry for the new club
        # Using season from joined_date if available
        season = None
        if new_registration.joined_date:
            year = new_registration.joined_date.year
            season = f"{year}/{year + 1}"

        PlayerCareer.objects.get_or_create(
            player=player,
            club=new_registration.club,
            season=season,
            defaults={
                "appearances": 0,
                "starts": 0,
                "minutes_played": 0,
                "goals": 0,
                "assists": 0,
                "yellow_cards": 0,
                "red_cards": 0,
            },
        )


class TransferError(Exception):
    """Raised when a transfer operation fails."""
    pass
