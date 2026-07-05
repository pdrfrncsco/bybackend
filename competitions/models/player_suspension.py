"""
BOLAYETU — PlayerSuspension Model

Represents an automatic or manual suspension for a player.
Suspensions can result from:
    - Accumulation of yellow cards (e.g., 5 yellows = 1 match suspension)
    - Direct red card
    - Two yellow cards in the same match (yellow-red)
    - Manual disciplinary action

Architecture:
    - PlayerSuspension is tenant-scoped (linked to competition/tenant)
    - Tracks suspension type, duration, and status
    - Integrates with FairPlayService for automatic suspension generation
"""

from django.db import models
from django.utils import timezone
from common.models import BaseModel


class PlayerSuspension(BaseModel):
    """
    Represents a player suspension in a competition.
    
    Suspensions are automatically generated when card thresholds are reached
    or can be manually added for disciplinary actions.
    """

    class SuspensionType(models.TextChoices):
        YELLOW_ACCUMULATION = "yellow_accumulation", "Acumulação de Cartões Amarelos"
        RED_CARD = "red_card", "Cartão Vermelho Direto"
        YELLOW_RED = "yellow_red", "Segundo Amarelo / Vermelho"
        DISCIPLINARY = "disciplinary", "Ação Disciplinar"
        MANUAL = "manual", "Suspensão Manual"

    class SuspensionStatus(models.TextChoices):
        PENDING = "pending", "Pendente"
        ACTIVE = "active", "Ativa"
        SERVED = "served", "Cumprida"
        CANCELLED = "cancelled", "Cancelada"
        APPEALED = "appealed", "Em Recurso"

    # ─── Core Relations ─────────────────────────────────────────────────────
    tenant = models.ForeignKey(
        "core.Tenant",
        on_delete=models.CASCADE,
        related_name="player_suspensions",
        verbose_name="Organization",
    )
    competition = models.ForeignKey(
        "competitions.Competition",
        on_delete=models.CASCADE,
        related_name="player_suspensions",
        verbose_name="Competition",
    )
    player = models.ForeignKey(
        "players.Player",
        on_delete=models.CASCADE,
        related_name="suspensions",
        verbose_name="Player",
    )
    club = models.ForeignKey(
        "clubs.Club",
        on_delete=models.CASCADE,
        related_name="player_suspensions",
        verbose_name="Club",
        help_text="The club the player was registered with when suspended.",
    )
    
    # Trigger match (if applicable)
    trigger_match = models.ForeignKey(
        "competitions.Match",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="suspensions_triggered",
        verbose_name="Trigger Match",
        help_text="The match where the card/event occurred (if applicable).",
    )
    trigger_event = models.ForeignKey(
        "competitions.MatchEvent",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="suspension_generated",
        verbose_name="Trigger Event",
        help_text="The specific match event that triggered this suspension.",
    )

    # ─── Suspension Details ──────────────────────────────────────────────────
    suspension_type = models.CharField(
        max_length=30,
        choices=SuspensionType.choices,
        verbose_name="Suspension Type",
    )
    matches_suspended = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="Matches Suspended",
        help_text="Number of matches the player must miss.",
    )
    matches_served = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Matches Served",
        help_text="Number of matches already served.",
    )
    
    # ─── Status ───────────────────────────────────────────────────────────────
    status = models.CharField(
        max_length=20,
        choices=SuspensionStatus.choices,
        default=SuspensionStatus.PENDING,
        verbose_name="Status",
    )
    
    # ─── Dates ────────────────────────────────────────────────────────────────
    effective_from = models.DateField(
        verbose_name="Effective From",
        help_text="Date from which the suspension is effective.",
    )
    effective_until = models.DateField(
        null=True,
        blank=True,
        verbose_name="Effective Until",
        help_text="Date until which the suspension is effective (if fixed period).",
    )
    served_on = models.DateField(
        null=True,
        blank=True,
        verbose_name="Served On",
        help_text="Date when the suspension was fully served.",
    )
    
    # ─── Additional Info ──────────────────────────────────────────────────────
    reason = models.CharField(
        max_length=500,
        blank=True,
        default="",
        verbose_name="Reason",
        help_text="Detailed reason for the suspension.",
    )
    notes = models.TextField(
        blank=True,
        default="",
        verbose_name="Internal Notes",
    )
    
    # ─── Audit ────────────────────────────────────────────────────────────────
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="suspensions_created",
        verbose_name="Created By",
    )
    cancelled_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="suspensions_cancelled",
        verbose_name="Cancelled By",
    )
    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Cancelled At",
    )
    cancellation_reason = models.CharField(
        max_length=500,
        blank=True,
        default="",
        verbose_name="Cancellation Reason",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Player Suspension"
        verbose_name_plural = "Player Suspensions"
        indexes = [
            models.Index(fields=["player", "competition", "status"]),
            models.Index(fields=["competition", "status"]),
            models.Index(fields=["club", "status"]),
        ]

    def __str__(self) -> str:
        return f"[{self.competition.name}] {self.player.full_name} - {self.get_suspension_type_display()} ({self.status})"

    @property
    def is_active(self) -> bool:
        """Check if suspension is currently active."""
        return self.status == self.SuspensionStatus.ACTIVE

    @property
    def is_pending(self) -> bool:
        """Check if suspension is pending."""
        return self.status == self.SuspensionStatus.PENDING

    @property
    def remaining_matches(self) -> int:
        """Calculate remaining matches to serve."""
        return max(0, self.matches_suspended - self.matches_served)

    @property
    def is_fully_served(self) -> bool:
        """Check if suspension has been fully served."""
        return self.matches_served >= self.matches_suspended

    def activate(self) -> None:
        """Activate a pending suspension."""
        if self.status == self.SuspensionStatus.PENDING:
            self.status = self.SuspensionStatus.ACTIVE
            self.save(update_fields=["status", "updated_at"])

    def serve_match(self) -> None:
        """
        Record that the player has served one match of the suspension.
        Automatically updates status to SERVED when fully served.
        """
        if self.status == self.SuspensionStatus.ACTIVE:
            self.matches_served += 1
            if self.is_fully_served:
                self.status = self.SuspensionStatus.SERVED
                self.served_on = timezone.now().date()
            self.save(update_fields=["matches_served", "status", "served_on", "updated_at"])

    def cancel(self, user, reason: str = "") -> None:
        """Cancel an active or pending suspension."""
        if self.status in [self.SuspensionStatus.PENDING, self.SuspensionStatus.ACTIVE]:
            self.status = self.SuspensionStatus.CANCELLED
            self.cancelled_by = user
            self.cancelled_at = timezone.now()
            self.cancellation_reason = reason
            self.save(update_fields=["status", "cancelled_by", "cancelled_at", "cancellation_reason", "updated_at"])
