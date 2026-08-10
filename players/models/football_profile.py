from django.db import models

from common.models import BaseModel


class PlayerFootballProfile(BaseModel):
    """Football-specific profile extracted from Player.

    Stores position, physical and aggregated stats. Designed to be small and focused
    as part of Phase 2 decomposition.
    """

    class FootChoices(models.TextChoices):
        LEFT = "left", "Left"
        RIGHT = "right", "Right"
        BOTH = "both", "Both"

    player = models.OneToOneField(
        "players.Player",
        on_delete=models.CASCADE,
        related_name="football_profile",
        verbose_name="Player",
    )

    primary_position = models.CharField(max_length=20, null=True, blank=True, verbose_name="Primary Position")
    shirt_number = models.IntegerField(null=True, blank=True, verbose_name="Shirt Number")

    height_cm = models.IntegerField(null=True, blank=True, verbose_name="Height (cm)")
    weight_kg = models.IntegerField(null=True, blank=True, verbose_name="Weight (kg)")
    foot = models.CharField(max_length=10, choices=FootChoices.choices, null=True, blank=True, verbose_name="Preferred Foot")

    # Denormalized season/career aggregates (can be recalculated from registrations/match events)
    total_matches = models.IntegerField(default=0, verbose_name="Total Matches")
    total_goals = models.IntegerField(default=0, verbose_name="Total Goals")
    total_assists = models.IntegerField(default=0, verbose_name="Total Assists")

    class Meta:
        verbose_name = "Football Profile"
        verbose_name_plural = "Football Profiles"

    def __str__(self) -> str:
        try:
            return f"FootballProfile: {self.player.full_name}"
        except Exception:
            return f"FootballProfile: {self.player_id}"
