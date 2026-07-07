"""
BOLAYETU — Match Model

Represents an individual football match within a competition round.
This is tenant-scoped and links home and away clubs.
"""

from django.db import models
from common.models import BaseModel


class Match(BaseModel):
    """
    Represents a match fixture between two registered clubs in a competition.
    """

    class MatchStatus(models.TextChoices):
        SCHEDULED = "scheduled", "Agendado"
        LIVE = "live", "Em Curso"
        FINISHED = "finished", "Concluído"
        POSTPONED = "postponed", "Adiado"
        CANCELLED = "cancelled", "Cancelado"

    competition = models.ForeignKey(
        "competitions.Competition",
        on_delete=models.CASCADE,
        related_name="matches",
        verbose_name="Competition",
    )
    tenant = models.ForeignKey(
        "core.Tenant",
        on_delete=models.CASCADE,
        related_name="matches",
        verbose_name="Organization",
    )
    home_club = models.ForeignKey(
        "clubs.Club",
        on_delete=models.CASCADE,
        related_name="home_matches",
        verbose_name="Home Club",
    )
    away_club = models.ForeignKey(
        "clubs.Club",
        on_delete=models.CASCADE,
        related_name="away_matches",
        verbose_name="Away Club",
    )
    match_date = models.DateTimeField(verbose_name="Match Date/Time")
    round_number = models.IntegerField(default=1, verbose_name="Round Number")
    status = models.CharField(
        max_length=20,
        choices=MatchStatus.choices,
        default=MatchStatus.SCHEDULED,
        verbose_name="Status",
    )
    
    # Results (populated when status = finished or live)
    home_score = models.IntegerField(null=True, blank=True, verbose_name="Home Score")
    away_score = models.IntegerField(null=True, blank=True, verbose_name="Away Score")
    
    venue = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Venue/Stadium",
    )

    class Meta:
        ordering = ["round_number", "match_date"]
        verbose_name = "Match"
        verbose_name_plural = "Matches"

    def __str__(self) -> str:
        score_str = f" {self.home_score} - {self.away_score} " if self.home_score is not None else " vs "
        return f"[{self.competition.name} - Round {self.round_number}] {self.home_club.name}{score_str}{self.away_club.name}"
