"""
PlayerContractService

Handles creation, renewal, termination and verification of player contracts.
"""

import logging
from datetime import date
from typing import Optional

from django.db import transaction

from players.models import Player, PlayerContract
from players.events.types import publish_player_contract_signed, publish_player_contract_terminated

logger = logging.getLogger("players")


class PlayerContractService:
    """Service for managing player contracts."""

    @staticmethod
    @transaction.atomic
    def create_contract(
        player: Player,
        club,
        contract_type: str,
        start_date: date,
        end_date: date,
        tenant,
        salary: Optional[float] = None,
        currency: str = "USD",
        bonuses: Optional[dict] = None,
        release_clause: Optional[float] = None,
        has_image_rights: bool = False,
    ) -> PlayerContract:
        """Create a new contract for a player at a club.

        Raises PlayerContractError if an active contract already exists.
        """
        # Check for existing active contracts
        active = PlayerContract.objects.filter(
            player=player,
            club=club,
            status__in=[PlayerContract.ContractStatus.ACTIVE, PlayerContract.ContractStatus.DRAFT],
        ).first()
        if active:
            raise PlayerContractError(
                f"Player {player.full_name} already has an active contract at {club.name}."
            )

        contract = PlayerContract.objects.create(
            player=player,
            club=club,
            tenant=tenant,
            contract_type=contract_type,
            start_date=start_date,
            end_date=end_date,
            status=PlayerContract.ContractStatus.DRAFT,
            salary=salary,
            currency=currency,
            bonuses=bonuses or {},
            release_clause=release_clause,
            has_image_rights=has_image_rights,
        )

        logger.info(
            "Contract created: %s @ %s (%s–%s)",
            player.full_name,
            club.name,
            start_date,
            end_date,
        )
        return contract

    @staticmethod
    @transaction.atomic
    def sign_contract(
        contract: PlayerContract,
        signed_by_player: bool = False,
        signed_by_club: bool = False,
    ) -> PlayerContract:
        """Update signature status for a contract.

        Once both player and club sign, activate the contract.
        """
        contract.signed_by_player = contract.signed_by_player or signed_by_player
        contract.signed_by_club = contract.signed_by_club or signed_by_club

        if contract.signed_by_player and contract.signed_by_club:
            from django.utils import timezone
            contract.status = PlayerContract.ContractStatus.ACTIVE
            contract.signed_date = timezone.now()

        contract.save()

        if contract.is_fully_signed:
            logger.info(
                "Contract fully signed: %s @ %s",
                contract.player.full_name,
                contract.club.name,
            )
            try:
                publish_player_contract_signed(
                    contract.id,
                    contract.player.id,
                    contract.club.id,
                    contract.start_date.isoformat(),
                    contract.end_date.isoformat(),
                    tenant_id=contract.tenant.id,
                )
            except Exception:
                logger.exception("Failed to publish PlayerContractSigned event for %s", contract.id)

        return contract

    @staticmethod
    @transaction.atomic
    def terminate_contract(
        contract: PlayerContract,
        terminated_reason: Optional[str] = None,
    ) -> PlayerContract:
        """Terminate an active contract."""
        contract.status = PlayerContract.ContractStatus.TERMINATED
        contract.save()

        logger.info(
            "Contract terminated: %s @ %s (reason: %s)",
            contract.player.full_name,
            contract.club.name,
            terminated_reason or "not specified",
        )

        try:
            publish_player_contract_terminated(
                contract.id,
                contract.player.id,
                contract.club.id,
                terminated_reason or "",
                tenant_id=contract.tenant.id,
            )
        except Exception:
            logger.exception("Failed to publish PlayerContractTerminated event for %s", contract.id)

        return contract

    @staticmethod
    @transaction.atomic
    def renew_contract(
        contract: PlayerContract,
        new_end_date: date,
        renewal_bonuses: Optional[dict] = None,
    ) -> PlayerContract:
        """Renew an existing contract by extending its end date."""
        old_end = contract.end_date
        contract.contract_type = PlayerContract.ContractType.EXTENSION
        contract.end_date = new_end_date
        if renewal_bonuses:
            contract.bonuses.update(renewal_bonuses)
        contract.save()

        logger.info(
            "Contract renewed: %s @ %s (%s → %s)",
            contract.player.full_name,
            contract.club.name,
            old_end,
            new_end_date,
        )
        return contract

    @staticmethod
    def get_active_contract(player: Player, club) -> Optional[PlayerContract]:
        """Get the currently active contract for a player at a club."""
        return PlayerContract.objects.filter(
            player=player,
            club=club,
            status=PlayerContract.ContractStatus.ACTIVE,
        ).select_related("club", "tenant").first()

    @staticmethod
    def get_contracts_for_player(player: Player):
        """Get all contracts for a player, ordered by most recent."""
        return PlayerContract.objects.filter(player=player).select_related(
            "club", "tenant"
        ).order_by("-start_date")


class PlayerContractError(Exception):
    """Raised when a contract operation fails."""
    pass
