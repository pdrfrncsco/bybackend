"""
BOLAYETU — MatchLineup Model

Represents the lineup (starting XI and substitutes) for a club in a match.

Architecture:
    - MatchLineup is tenant-scoped
    - Each player entry has a position and shirt number
    - Status distinguishes between starter (titular) and substitute (suplente)
    - Captain and goalkeeper flags for special roles
"""

from django.db import models
from django.utils import timezone
from common.models import BaseModel


class MatchLineup(BaseModel):
    """
    Represents a player entry in a match lineup.
    
    Each entry links a player to a specific match and club,
    with their position, shirt number, and starter/substitute status.
    """

    class LineupStatus(models.TextChoices):
        STARTER = "starter", "Titular"
        SUBSTITUTE = "substitute", "Suplente"
        UNUSED = "unused", "Não Utilizado"

    class Position(models.TextChoices):
        # Goalkeeper
        GK = "gk", "Guarda-Redes"
        # Defence
        CB = "cb", "Defesa Central"
        LB = "lb", "Defesa Esquerdo"
        RB = "rb", "Defesa Direito"
        LWB = "lwb", "Lateral Esquerdo"
        RWB = "rwb", "Lateral Direito"
        # Midfield
        CM = "cm", "Médio Centro"
        CDM = "cdm", "Médio Defensivo"
        CAM = "cam", "Médio Ofensivo"
        LM = "lm", "Médio Esquerdo"
        RM = "rm", "Médio Direito"
        LW = "lw", "Extremo Esquerdo"
        RW = "rw", "Extremo Direito"
        # Attack
        ST = "st", "Avançado"
        CF = "cf", "Ponta de Lança"

    # ─── Core Relations ─────────────────────────────────────────────────────
    tenant = models.ForeignKey(
        "core.Tenant",
        on_delete=models.CASCADE,
        related_name="match_lineups",
        verbose_name="Organization",
    )
    match = models.ForeignKey(
        "competitions.Match",
        on_delete=models.CASCADE,
        related_name="lineups",
        verbose_name="Match",
    )
    club = models.ForeignKey(
        "clubs.Club",
        on_delete=models.CASCADE,
        related_name="match_lineups",
        verbose_name="Club",
    )
    player = models.ForeignKey(
        "players.Player",
        on_delete=models.CASCADE,
        related_name="match_lineups",
        verbose_name="Player",
    )

    # ─── Lineup Details ──────────────────────────────────────────────────────
    status = models.CharField(
        max_length=20,
        choices=LineupStatus.choices,
        default=LineupStatus.SUBSTITUTE,
        verbose_name="Status",
        help_text="Starter, substitute, or unused.",
    )
    position = models.CharField(
        max_length=20,
        choices=Position.choices,
        verbose_name="Position",
        help_text="Position played in this match.",
    )
    shirt_number = models.PositiveSmallIntegerField(
        verbose_name="Shirt Number",
        help_text="Shirt number worn in this match.",
    )

    # ─── Special Roles ────────────────────────────────────────────────────────
    is_captain = models.BooleanField(
        default=False,
        verbose_name="Is Captain",
        help_text="Whether this player is the team captain.",
    )
    is_goalkeeper = models.BooleanField(
        default=False,
        verbose_name="Is Goalkeeper",
        help_text="Whether this player is the goalkeeper.",
    )

    # ─── Formation Position ───────────────────────────────────────────────────
    formation_position = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="Formation Position",
        help_text="Position in formation (1-11 for starters).",
    )

    # ─── Eligibility (Phase 3: Match Center) ─────────────────────────────────
    eligible = models.BooleanField(
        default=True,
        verbose_name="Is Eligible",
        help_text="Whether this player is eligible for this match.",
    )
    eligibility_warning = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Eligibility Warning",
        help_text="Warning message if player has eligibility issues.",
    )

    # ─── Stats (populated after match) ────────────────────────────────────────
    minutes_played = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="Minutes Played",
        help_text="Minutes played (populated after match).",
    )
    substituted_in_minute = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="Substituted In Minute",
        help_text="Minute when player came on (for substitutes).",
    )
    substituted_out_minute = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="Substituted Out Minute",
        help_text="Minute when player went off.",
    )

    # ─── Audit ────────────────────────────────────────────────────────────────
    submitted_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Submitted At",
    )
    submitted_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lineups_submitted",
        verbose_name="Submitted By",
    )

    class Meta:
        ordering = ["match", "club", "-status", "formation_position"]
        verbose_name = "Match Lineup"
        verbose_name_plural = "Match Lineups"
        indexes = [
            models.Index(fields=["match", "club"]),
            models.Index(fields=["match", "club", "status"]),
            models.Index(fields=["player", "match"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["match", "club", "player"],
                name="unique_player_in_match_lineup",
            ),
            models.UniqueConstraint(
                fields=["match", "club", "shirt_number"],
                name="unique_shirt_number_in_match_lineup",
            ),
        ]

    def __str__(self) -> str:
        status_str = " (T)" if self.status == self.LineupStatus.STARTER else " (S)"
        return f"[{self.match}] {self.club.name} #{self.shirt_number} {self.player.full_name}{status_str}"

    @property
    def is_starter(self) -> bool:
        """Check if player is in starting XI."""
        return self.status == self.LineupStatus.STARTER

    @property
    def is_substitute(self) -> bool:
        """Check if player is a substitute."""
        return self.status == self.LineupStatus.SUBSTITUTE

    @property
    def played(self) -> bool:
        """Check if player actually played (minutes_played > 0)."""
        return self.minutes_played is not None and self.minutes_played > 0


class LineupSubmission(BaseModel):
    """
    Tracks the submission of a complete lineup for a club in a match.
    
    Used to track when lineups were submitted and their status.
    """

    class SubmissionStatus(models.TextChoices):
        PENDING = "pending", "Pendente"
        SUBMITTED = "submitted", "Submetida"
        CONFIRMED = "confirmed", "Confirmada"
        LOCKED = "locked", "Bloqueada"

    tenant = models.ForeignKey(
        "core.Tenant",
        on_delete=models.CASCADE,
        related_name="lineup_submissions",
        verbose_name="Organization",
    )
    match = models.ForeignKey(
        "competitions.Match",
        on_delete=models.CASCADE,
        related_name="lineup_submissions",
        verbose_name="Match",
    )
    club = models.ForeignKey(
        "clubs.Club",
        on_delete=models.CASCADE,
        related_name="lineup_submissions",
        verbose_name="Club",
    )

    status = models.CharField(
        max_length=20,
        choices=SubmissionStatus.choices,
        default=SubmissionStatus.PENDING,
        verbose_name="Status",
    )
    formation = models.CharField(
        max_length=10,
        blank=True,
        default="",
        verbose_name="Formation",
        help_text="Formation used (e.g., '4-3-3', '4-4-2').",
    )

    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Submitted At",
    )
    submitted_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lineup_submissions_done",
        verbose_name="Submitted By",
    )

    confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Confirmed At",
    )
    confirmed_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lineup_submissions_confirmed",
        verbose_name="Confirmed By",
    )

    notes = models.TextField(
        blank=True,
        default="",
        verbose_name="Notes",
    )

    class Meta:
        ordering = ["match", "club"]
        verbose_name = "Lineup Submission"
        verbose_name_plural = "Lineup Submissions"
        constraints = [
            models.UniqueConstraint(
                fields=["match", "club"],
                name="unique_lineup_submission_per_match_club",
            ),
        ]

    def __str__(self) -> str:
        return f"[{self.match}] {self.club.name} Lineup ({self.get_status_display()})"

    def submit(self, user) -> None:
        """Mark lineup as submitted."""
        self.status = self.SubmissionStatus.SUBMITTED
        self.submitted_at = timezone.now()
        self.submitted_by = user
        self.save(update_fields=["status", "submitted_at", "submitted_by", "updated_at"])

    def confirm(self, user) -> None:
        """Confirm the lineup."""
        self.status = self.SubmissionStatus.CONFIRMED
        self.confirmed_at = timezone.now()
        self.confirmed_by = user
        self.save(update_fields=["status", "confirmed_at", "confirmed_by", "updated_at"])

    def lock(self) -> None:
        """Lock the lineup (no further changes allowed)."""
        self.status = self.SubmissionStatus.LOCKED
        self.save(update_fields=["status", "updated_at"])
