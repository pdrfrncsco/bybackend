"""
BOLAYETU — Transfer Model

Represents player transfers between clubs with support for permanent transfers and loans.

Architecture:
    - Transfer is tenant-scoped
    - Tracks all player movements: permanent transfers, loans, returns
    - Maintains approval workflow for club-to-club transfers
    - Loan end dates trigger automatic returns
    - PlayerRegistration is created/updated to reflect status
"""

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta

from common.models import BaseModel


class Transfer(BaseModel):
    """
    Represents a player transfer between clubs.
    
    Supports:
        - Permanent transfers (club to club)
        - Loans with automatic return mechanism
        - Free agent signings
        - Auto-return on loan end date
    """

    class TransferType(models.TextChoices):
        PERMANENT = "permanent", "Permanent Transfer"
        LOAN = "loan", "Loan"
        FREE_AGENT = "free_agent", "Free Agent Signing"

    class TransferStatus(models.TextChoices):
        PENDING = "pending", "Awaiting Approval"
        APPROVED = "approved", "Approved"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        RETURNED = "returned", "Loan Returned"

    # ─── Core Relations ────────────────────────────────────────────────────
    tenant = models.ForeignKey(
        "core.Tenant",
        on_delete=models.CASCADE,
        related_name="transfers",
        verbose_name="Organization",
    )
    player = models.ForeignKey(
        "players.Player",
        on_delete=models.CASCADE,
        related_name="club_transfers",
        verbose_name="Player",
    )

    # ─── Transfer Details ─────────────────────────────────────────────────
    from_club = models.ForeignKey(
        "clubs.Club",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="outgoing_transfers",
        verbose_name="From Club",
        help_text="Club player is leaving (null for free agent signings).",
    )
    to_club = models.ForeignKey(
        "clubs.Club",
        on_delete=models.CASCADE,
        related_name="incoming_transfers",
        verbose_name="To Club",
        help_text="Club player is joining.",
    )

    transfer_type = models.CharField(
        max_length=20,
        choices=TransferType.choices,
        default=TransferType.PERMANENT,
        verbose_name="Transfer Type",
        help_text="Permanent, loan, or free agent signing.",
    )

    # ─── Transfer Status & Workflow ────────────────────────────────────────
    status = models.CharField(
        max_length=20,
        choices=TransferStatus.choices,
        default=TransferStatus.PENDING,
        verbose_name="Status",
        help_text="Workflow status: pending → approved → completed.",
    )

    # ─── Dates ─────────────────────────────────────────────────────────────
    transfer_date = models.DateField(
        verbose_name="Transfer Date",
        help_text="Date transfer becomes effective.",
    )
    announced_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Announced At",
    )

    # ─── Loan Specific ────────────────────────────────────────────────────
    loan_end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Loan End Date",
        help_text="Date when loan ends and player returns to origin club.",
    )
    loan_return_mandatory = models.BooleanField(
        default=True,
        verbose_name="Loan Return Mandatory",
        help_text="Whether player automatically returns on loan end date.",
    )

    # ─── Financial Terms ──────────────────────────────────────────────────
    fee = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Transfer Fee",
        help_text="Transfer fee in base currency (null for free agents/loans).",
    )
    salary_contribution = models.BooleanField(
        default=False,
        verbose_name="From Club Contributes Salary",
        help_text="Whether origin club contributes to salary during loan.",
    )

    # ─── Approval Workflow ─────────────────────────────────────────────────
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Approved At",
    )
    approved_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transfers_approved",
        verbose_name="Approved By",
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Completed At",
    )
    completed_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transfers_completed",
        verbose_name="Completed By",
    )

    # ─── Rejection/Cancellation ───────────────────────────────────────────
    rejected_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Rejected At",
    )
    rejected_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transfers_rejected",
        verbose_name="Rejected By",
    )
    rejection_reason = models.TextField(
        blank=True,
        default="",
        verbose_name="Rejection Reason",
    )

    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Cancelled At",
    )
    cancellation_reason = models.TextField(
        blank=True,
        default="",
        verbose_name="Cancellation Reason",
    )

    # ─── Loan Return ──────────────────────────────────────────────────────
    returned_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Returned At",
        help_text="Date loan was completed and player returned.",
    )
    made_permanent = models.BooleanField(
        default=False,
        verbose_name="Made Permanent",
        help_text="Whether loan was converted to permanent transfer.",
    )

    # ─── Notes & Documentation ───────────────────────────────────────────
    notes = models.TextField(
        blank=True,
        default="",
        verbose_name="Notes",
    )

    class Meta:
        ordering = ["-transfer_date", "-created_at"]
        verbose_name = "Transfer"
        verbose_name_plural = "Transfers"
        indexes = [
            models.Index(fields=["tenant", "status", "-transfer_date"]),
            models.Index(fields=["player", "status"]),
            models.Index(fields=["from_club", "status"]),
            models.Index(fields=["to_club", "status"]),
            models.Index(fields=["transfer_type", "status"]),
        ]

    def __str__(self) -> str:
        if self.from_club:
            return f"{self.player.full_name}: {self.from_club.name} → {self.to_club.name} ({self.get_transfer_type_display()})"
        else:
            return f"{self.player.full_name}: Free Agent → {self.to_club.name}"

    # ─── Status Checks ────────────────────────────────────────────────────

    @property
    def is_pending(self) -> bool:
        """Check if transfer is awaiting approval."""
        return self.status == self.TransferStatus.PENDING

    @property
    def is_approved(self) -> bool:
        """Check if transfer is approved."""
        return self.status == self.TransferStatus.APPROVED

    @property
    def is_completed(self) -> bool:
        """Check if transfer is completed."""
        return self.status == self.TransferStatus.COMPLETED

    @property
    def is_loan(self) -> bool:
        """Check if transfer is a loan."""
        return self.transfer_type == self.TransferType.LOAN

    @property
    def is_free_agent_signing(self) -> bool:
        """Check if transfer is free agent signing."""
        return self.transfer_type == self.TransferType.FREE_AGENT

    @property
    def loan_is_active(self) -> bool:
        """Check if loan is currently active."""
        if not self.is_loan or not self.is_completed:
            return False
        if not self.loan_end_date:
            return False
        return timezone.now().date() < self.loan_end_date

    @property
    def loan_is_expired(self) -> bool:
        """Check if loan end date has passed."""
        if not self.is_loan:
            return False
        if not self.loan_end_date:
            return False
        return timezone.now().date() >= self.loan_end_date

    @property
    def requires_approval(self) -> bool:
        """Check if transfer requires approval from origin club."""
        # Free agents and loans don't require approval
        return self.from_club is not None and self.transfer_type == self.TransferType.PERMANENT

    # ─── State Transitions ─────────────────────────────────────────────────

    def approve(self, user) -> None:
        """Mark transfer as approved."""
        if self.status not in [self.TransferStatus.PENDING]:
            raise ValidationError(f"Cannot approve transfer with status {self.get_status_display()}")
        
        self.status = self.TransferStatus.APPROVED
        self.approved_at = timezone.now()
        self.approved_by = user
        self.save(update_fields=["status", "approved_at", "approved_by", "updated_at"])

    def reject(self, user, reason: str = "") -> None:
        """Mark transfer as rejected."""
        if self.status not in [self.TransferStatus.PENDING, self.TransferStatus.APPROVED]:
            raise ValidationError(f"Cannot reject transfer with status {self.get_status_display()}")
        
        self.status = self.TransferStatus.CANCELLED
        self.rejected_at = timezone.now()
        self.rejected_by = user
        self.rejection_reason = reason
        self.save(update_fields=["status", "rejected_at", "rejected_by", "rejection_reason", "updated_at"])

    def complete(self, user) -> None:
        """Mark transfer as completed."""
        if self.status not in [self.TransferStatus.PENDING, self.TransferStatus.APPROVED]:
            raise ValidationError(f"Cannot complete transfer with status {self.get_status_display()}")
        
        self.status = self.TransferStatus.COMPLETED
        self.completed_at = timezone.now()
        self.completed_by = user
        self.save(update_fields=["status", "completed_at", "completed_by", "updated_at"])

    def cancel(self, reason: str = "") -> None:
        """Cancel a transfer."""
        if self.status in [self.TransferStatus.CANCELLED, self.TransferStatus.RETURNED]:
            raise ValidationError(f"Cannot cancel transfer with status {self.get_status_display()}")
        
        self.status = self.TransferStatus.CANCELLED
        self.cancelled_at = timezone.now()
        self.cancellation_reason = reason
        self.save(update_fields=["status", "cancelled_at", "cancellation_reason", "updated_at"])

    def make_return(self, user) -> None:
        """Mark loan as returned."""
        if not self.is_loan:
            raise ValidationError("Only loans can be returned")
        if self.status != self.TransferStatus.COMPLETED:
            raise ValidationError(f"Cannot return loan with status {self.get_status_display()}")
        
        self.status = self.TransferStatus.RETURNED
        self.returned_at = timezone.now()
        self.save(update_fields=["status", "returned_at", "updated_at"])

    def make_permanent(self, user, fee: float = None) -> None:
        """Convert loan to permanent transfer."""
        if not self.is_loan:
            raise ValidationError("Only loans can be made permanent")
        if self.status != self.TransferStatus.COMPLETED:
            raise ValidationError(f"Cannot convert loan with status {self.get_status_display()}")
        
        self.transfer_type = self.TransferType.PERMANENT
        self.made_permanent = True
        self.loan_end_date = None
        if fee is not None:
            self.fee = fee
        self.save(update_fields=["transfer_type", "made_permanent", "loan_end_date", "fee", "updated_at"])
