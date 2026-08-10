from django.db import models

from common.models import BaseModel


class PlayerSeasonStatistics(BaseModel):
    """Aggregated season statistics for a player (per club/competition/season)."""

    player = models.ForeignKey(
        "players.Player",
        on_delete=models.CASCADE,
        related_name="season_statistics",
        verbose_name="Player",
    )

    season = models.CharField(max_length=32, null=True, blank=True, verbose_name="Season")

    club = models.ForeignKey(
        "clubs.Club",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="player_season_statistics",
        verbose_name="Club",
    )

    competition = models.ForeignKey(
        "competitions.Competition",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="player_season_statistics",
        verbose_name="Competition",
    )

    appearances = models.IntegerField(default=0, verbose_name="Appearances")
    starts = models.IntegerField(default=0, verbose_name="Starts")
    minutes = models.IntegerField(default=0, verbose_name="Minutes Played")
    goals = models.IntegerField(default=0, verbose_name="Goals")
    assists = models.IntegerField(default=0, verbose_name="Assists")
    shots = models.IntegerField(default=0, verbose_name="Shots")
    shots_on_target = models.IntegerField(default=0, verbose_name="Shots on Target")
    yellow_cards = models.IntegerField(default=0, verbose_name="Yellow Cards")
    red_cards = models.IntegerField(default=0, verbose_name="Red Cards")

    class Meta:
        verbose_name = "Player Season Statistics"
        verbose_name_plural = "Player Season Statistics"
        ordering = ["-season", "-appearances"]
        unique_together = [("player", "club", "season", "competition")]

    def __str__(self) -> str:
        return f"{self.player.full_name} — {self.season} @ {self.club.name if self.club else '<unknown>'}"
