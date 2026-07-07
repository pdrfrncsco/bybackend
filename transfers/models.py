"""
BOLAYETU — Transfer Model

Represents a transfer request and completion of a Player between Clubs.
"""

from django.db import models
from common.models import BaseModel


class Transfer(BaseModel):
    """
    Represents the transfer of a player from one club (from_club) to another (to_club).
    
    The transfer can be:
        - Free Agent to Club (from_club is Null)
        - Club to Club
        
    It goes through a workflow:
        - PENDING: Request created by target club.
        - APPROVED: Approved by origin club (required only if from_club is set).
        - REJECTED: Rejected by origin club.
        - COMPLETED: Old registration deactivated, new registration activated.
    """

    class TransferStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        COMPLETED = "completed", "Completed"

    # Player (global)
    player = models.ForeignKey(
        "players.Player",
        on_delete=models.CASCADE,
        related_name="transfers",
        verbose_name="Player",
    )

    # Origin Club (tenant-scoped)
    from_club = models.ForeignKey(
        "clubs.Club",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transfers_out",
        verbose_name="From Club",
    )

    # Destination Club (tenant-scoped)
    to_club = models.ForeignKey(
        "clubs.Club",
        on_delete=models.CASCADE,
        related_name="transfers_in",
        verbose_name="To Club",
    )

    # Origin Tenant (for isolation and query efficiency)
    from_tenant = models.ForeignKey(
        "core.Tenant",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transfers_out",
        verbose_name="From Tenant",
    )

    # Destination Tenant
    to_tenant = models.ForeignKey(
        "core.Tenant",
        on_delete=models.CASCADE,
        related_name="transfers_in",
        verbose_name="To Tenant",
    )

    # Optional competition target for the new registration
    competition = models.ForeignKey(
        "competitions.Competition",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transfers",
        verbose_name="Competition",
    )

    # New registration details
    joined_date = models.DateField(verbose_name="Joined Date")
    shirt_number = models.IntegerField(null=True, blank=True, verbose_name="Shirt Number")
    
    # Financials
    fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Transfer Fee",
    )

    # Status & Dates
    status = models.CharField(
        max_length=20,
        choices=TransferStatus.choices,
        default=TransferStatus.PENDING,
        verbose_name="Status",
    )
    request_date = models.DateTimeField(auto_now_add=True, verbose_name="Request Date")
    completed_date = models.DateTimeField(null=True, blank=True, verbose_name="Completed Date")
    rejection_reason = models.TextField(null=True, blank=True, verbose_name="Rejection Reason")

    class Meta:
        ordering = ["-request_date"]
        verbose_name = "Transfer"
        verbose_name_plural = "Transfers"
        indexes = [
            models.Index(fields=["player"]),
            models.Index(fields=["status"]),
            models.Index(fields=["from_club"]),
            models.Index(fields=["to_club"]),
        ]

    def __str__(self) -> str:
        from_club_name = self.from_club.name if self.from_club else "Free Agent"
        return f"Transfer of {self.player.full_name}: {from_club_name} → {self.to_club.name} ({self.status})"
