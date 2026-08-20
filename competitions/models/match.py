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
        PRE_MATCH = "pre_match", "Pré-jogo"
        LIVE = "live", "Em Curso"
        HALFTIME = "halftime", "Intervalo"
        FINISHED = "finished", "Concluído"
        ARCHIVED = "archived", "Arquivado"
        POSTPONED = "postponed", "Adiado"
        CANCELLED = "cancelled", "Cancelado"
        WALKOVER = "walkover", "Walkover"

    class MatchPeriod(models.TextChoices):
        FIRST_HALF = "first_half", "1º Tempo"
        SECOND_HALF = "second_half", "2º Tempo"
        EXTRA_TIME = "extra_time", "Prorrogação"
        PENALTIES = "penalties", "Penaltis"
        HALFTIME = "halftime", "Intervalo"
        FULLTIME = "fulltime", "Fim de jogo"

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
    round_name = models.CharField(max_length=100, null=True, blank=True, verbose_name="Round Name")
    phase = models.CharField(max_length=50, null=True, blank=True, verbose_name="Phase")
    group_id = models.CharField(max_length=64, null=True, blank=True, verbose_name="Group ID")
    status = models.CharField(
        max_length=20,
        choices=MatchStatus.choices,
        default=MatchStatus.SCHEDULED,
        verbose_name="Status",
    )
    current_period = models.CharField(
        max_length=20,
        choices=MatchPeriod.choices,
        null=True,
        blank=True,
        default=None,
        verbose_name="Current Period",
    )
    current_minute = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Current Minute",
        help_text="Live minute value for the current period.",
    )
    clock_running = models.BooleanField(
        default=False,
        verbose_name="Clock Running",
    )
    clock_started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Clock Started At",
    )
    clock_elapsed_seconds = models.PositiveIntegerField(
        default=0,
        verbose_name="Clock Elapsed Seconds",
        help_text="Elapsed seconds in the current period when the clock is paused or last synchronised.",
    )
    stoppage_time_minutes = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Stoppage Time Minutes",
    )
    clock_version = models.PositiveIntegerField(
        default=0,
        verbose_name="Clock Version",
    )
    
    # Results (populated when status = finished or live)
    home_score = models.IntegerField(null=True, blank=True, verbose_name="Home Score")
    away_score = models.IntegerField(null=True, blank=True, verbose_name="Away Score")
    home_penalty_score = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="Home Penalty Shootout Score")
    away_penalty_score = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="Away Penalty Shootout Score")
    
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
