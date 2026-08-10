from django.db import models

from common.models import BaseModel


class PlayerCareer(BaseModel):
    """Aggregated career record for a player in a club/season/competition."""

    player = models.ForeignKey(
        "players.Player",
        on_delete=models.CASCADE,
        related_name="careers",
        verbose_name="Player",
    )

    club = models.ForeignKey(
        "clubs.Club",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="player_careers",
        verbose_name="Club",
    )

    season = models.CharField(max_length=32, null=True, blank=True, verbose_name="Season")

    competition = models.ForeignKey(
        "competitions.Competition",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="player_careers",
        verbose_name="Competition",
    )

    position = models.CharField(max_length=20, null=True, blank=True, verbose_name="Position")

    appearances = models.IntegerField(default=0, verbose_name="Appearances")
    starts = models.IntegerField(default=0, verbose_name="Starts")
    minutes_played = models.IntegerField(default=0, verbose_name="Minutes Played")
    goals = models.IntegerField(default=0, verbose_name="Goals")
    assists = models.IntegerField(default=0, verbose_name="Assists")
    yellow_cards = models.IntegerField(default=0, verbose_name="Yellow Cards")
    red_cards = models.IntegerField(default=0, verbose_name="Red Cards")

    class Meta:
        verbose_name = "Player Career"
        verbose_name_plural = "Player Careers"
        ordering = ["-season", "-appearances"]
        unique_together = [("player", "club", "season", "competition")]

    def __str__(self) -> str:
        club_name = self.club.name if self.club else "<unknown>"
        return f"{self.player.full_name} @ {club_name} ({self.season})"