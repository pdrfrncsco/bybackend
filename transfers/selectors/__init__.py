"""
BOLAYETU — Transfer Selectors

Read-only query methods for transfers.
"""

from typing import Optional
from django.db.models import QuerySet, Q

from transfers.models import Transfer


class TransferSelector:
    """Read-only queries for Transfer data."""

    @staticmethod
    def get_by_id(transfer_id) -> Optional[Transfer]:
        """Get a transfer by ID."""
        try:
            return Transfer.objects.select_related(
                "player", "from_club", "to_club", "competition"
            ).get(id=transfer_id)
        except Transfer.DoesNotExist:
            return None

    @staticmethod
    def list_all() -> QuerySet:
        """List all transfers ordered by request date (newest first)."""
        return Transfer.objects.select_related(
            "player", "from_club", "to_club", "competition"
        ).order_by("-request_date")

    @staticmethod
    def list_by_status(status: str) -> QuerySet:
        """List transfers filtered by status."""
        return Transfer.objects.filter(status=status).select_related(
            "player", "from_club", "to_club", "competition"
        ).order_by("-request_date")

    @staticmethod
    def list_by_player(player_id) -> QuerySet:
        """List all transfers for a specific player."""
        return Transfer.objects.filter(player_id=player_id).select_related(
            "from_club", "to_club", "competition"
        ).order_by("-request_date")

    @staticmethod
    def list_outgoing_transfers(club_id) -> QuerySet:
        """
        List all outgoing transfers for a club.

        These are transfers WHERE the club is the origin (from_club).
        Includes PENDING (awaiting club's approval), APPROVED, REJECTED, COMPLETED.
        """
        return Transfer.objects.filter(from_club_id=club_id).select_related(
            "player", "to_club", "competition"
        ).order_by("-request_date")

    @staticmethod
    def list_incoming_transfers(club_id) -> QuerySet:
        """
        List all incoming transfers for a club.

        These are transfers WHERE the club is the destination (to_club).
        """
        return Transfer.objects.filter(to_club_id=club_id).select_related(
            "player", "from_club", "competition"
        ).order_by("-request_date")

    @staticmethod
    def list_pending_for_club(club_id) -> QuerySet:
        """
        List PENDING transfers that require action from a club.

        For origin club (from_club): pending approval requests.
        """
        return Transfer.objects.filter(
            from_club_id=club_id,
            status=Transfer.TransferStatus.PENDING,
        ).select_related(
            "player", "to_club", "competition"
        ).order_by("-request_date")

    @staticmethod
    def list_by_tenant(tenant_id) -> QuerySet:
        """
        List all transfers for a tenant (organization).

        Includes both incoming and outgoing transfers.
        """
        return Transfer.objects.filter(
            Q(from_tenant_id=tenant_id) | Q(to_tenant_id=tenant_id)
        ).select_related(
            "player", "from_club", "to_club", "competition"
        ).order_by("-request_date")

    @staticmethod
    def list_recent_completed(limit: int = 10) -> QuerySet:
        """List most recent completed transfers."""
        return Transfer.objects.filter(
            status=Transfer.TransferStatus.COMPLETED
        ).select_related(
            "player", "from_club", "to_club", "competition"
        ).order_by("-completed_date")[:limit]

    @staticmethod
    def get_player_current_transfer(player_id) -> Optional[Transfer]:
        """Get the most recent transfer for a player (if any)."""
        return Transfer.objects.filter(player_id=player_id).order_by("-request_date").first()
