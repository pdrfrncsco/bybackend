"""
BOLAYETU — National Team Call-Up Model

Represents a player's call-up to a national team.
Important for career tracking and international recognition.
"""

from django.db import models
from common.models import BaseModel


class NationalTeamCallUp(BaseModel):
    """Represents a player's call-up to a national team."""

    class Category(models.TextChoices):
        SENIOR = "senior", "Seleção Principal"
        U23 = "u23", "Sub-23"
        U20 = "u20", "Sub-20"
        U17 = "u17", "Sub-17"
        U15 = "u15", "Sub-15"

    class CallUpStatus(models.TextChoices):
        CALLED = "called", "Convocado"
        RELEASED = "released", "Libertado"
        DECLINED = "declined", "Recusou"
        INJURED = "injured", "Lesionado"
        COMPLETED = "completed", "Concluído"

    # Relations
    player = models.ForeignKey(
        "players.Player",
        on_delete=models.CASCADE,
        related_name="national_team_call_ups",
        verbose_name="Jogador",
    )
    competition = models.ForeignKey(
        "competitions.Competition",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="national_team_call_ups",
        verbose_name="Competição",
    )

    # National Team Details
    national_team = models.CharField(
        max_length=3,
        verbose_name="Seleção Nacional",
        help_text="Código ISO 3166-1 alpha-3 do país",
    )
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.SENIOR,
        verbose_name="Categoria",
    )

    # Dates
    call_up_date = models.DateField(
        verbose_name="Data de Convocatória",
    )
    release_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data de Libertação",
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=CallUpStatus.choices,
        default=CallUpStatus.CALLED,
        verbose_name="Estado",
    )

    # Statistics
    caps = models.IntegerField(
        default=0,
        verbose_name="Internacionalizações",
        help_text="Número de jogos disputados pela seleção",
    )
    goals = models.IntegerField(
        default=0,
        verbose_name="Golos",
        help_text="Golos marcados pela seleção",
    )
    assists = models.IntegerField(
        default=0,
        verbose_name="Assistências",
        help_text="Assistências pela seleção",
    )

    # Additional Info
    notes = models.TextField(
        blank=True,
        verbose_name="Notas",
    )

    class Meta:
        verbose_name = "Convocatória de Seleção"
        verbose_name_plural = "Convocatórias de Seleção"
        ordering = ["-call_up_date"]
        indexes = [
            models.Index(fields=["player", "call_up_date"]),
            models.Index(fields=["national_team", "category"]),
        ]

    def __str__(self) -> str:
        return f"{self.player.full_name} → {self.national_team} ({self.category})"

    @property
    def is_active(self) -> bool:
        """Check if call-up is currently active."""
        from datetime import date
        if self.status != self.CallUpStatus.CALLED:
            return False
        if self.release_date and self.release_date < date.today():
            return False
        return True

    def get_national_team_name(self) -> str:
        """Get the national team country name."""
        # Could be enhanced with a country lookup table
        return self.national_team
