"""
BOLAYETU — PlayerTrainingHistory Model

Represents training/development history for players (clubs, academies).
Critical for calculating EPP (Education & Productivity Payouts) and Solidarity Contribution.
"""

from django.db import models
from common.models import BaseModel


class PlayerTrainingHistory(BaseModel):
    """Training history entry for a player (club/academy)."""

    class TrainingCategory(models.TextChoices):
        AMATEUR = "amateur", "Amador"
        YOUTH = "youth", "Futebol de Base"
        ACADEMY = "academy", "Academia"
        PROFESSIONAL = "professional", "Profissional"

    # Relations
    player = models.ForeignKey(
        "players.Player",
        on_delete=models.CASCADE,
        related_name="training_history",
        verbose_name="Jogador",
    )
    club = models.ForeignKey(
        "clubs.Club",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="player_training_history",
        verbose_name="Clube",
    )

    # Alternative to club: academy/independent entity
    academy_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Nome da Academia",
        help_text="Se não for um clube registado no sistema",
    )

    # Training Details
    country = models.CharField(
        max_length=3,
        verbose_name="País",
        help_text="ISO 3166-1 alpha-3",
    )
    training_category = models.CharField(
        max_length=20,
        choices=TrainingCategory.choices,
        default=TrainingCategory.AMATEUR,
        verbose_name="Categoria de Treino",
    )

    # Dates
    start_date = models.DateField(verbose_name="Data de Início")
    end_date = models.DateField(null=True, blank=True, verbose_name="Data de Término")

    # Verification
    verified = models.BooleanField(default=False, verbose_name="Verificado")
    verified_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_player_training_history",
        verbose_name="Verificado Por",
    )
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data de Verificação",
    )

    # Documentation
    training_certificate = models.ForeignKey(
        "media_assets.MediaAsset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="player_training_certificates",
        verbose_name="Certificado",
    )

    # Notes
    notes = models.TextField(blank=True, verbose_name="Notas")

    class Meta:
        verbose_name = "Historial de Treino do Jogador"
        verbose_name_plural = "Historials de Treino do Jogador"
        ordering = ["-start_date"]
        indexes = [
            models.Index(fields=["player", "start_date"]),
            models.Index(fields=["country", "training_category"]),
        ]

    def __str__(self) -> str:
        entity = self.club.name if self.club else self.academy_name or "<sem entidade>"
        return f"{self.player.full_name} @ {entity} ({self.start_date.year}–{self.end_date.year if self.end_date else 'present'})"

    @property
    def duration_years(self) -> float:
        """Calculate duration in years."""
        from datetime import date as date_class
        end = self.end_date or date_class.today()
        days = (end - self.start_date).days
        return days / 365.25
