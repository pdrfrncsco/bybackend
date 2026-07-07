"""
BOLAYETU — Standing Model

Represents a club's standing/ranking entry in a specific competition table.
This is tenant-scoped, and is recalculable on demand based on match results.
"""

from django.db import models
from common.models import BaseModel


class Standing(BaseModel):
    """
    Represents a row in the competition standings/league table.
    """

    competition = models.ForeignKey(
        "competitions.Competition",
        on_delete=models.CASCADE,
        related_name="standings",
        verbose_name="Competition",
    )
    club = models.ForeignKey(
        "clubs.Club",
        on_delete=models.CASCADE,
        related_name="standings",
        verbose_name="Club",
    )
    tenant = models.ForeignKey(
        "core.Tenant",
        on_delete=models.CASCADE,
        related_name="standings",
        verbose_name="Organization",
    )
    
    # Stats
    played = models.IntegerField(default=0, verbose_name="Matches Played")
    won = models.IntegerField(default=0, verbose_name="Matches Won")
    drawn = models.IntegerField(default=0, verbose_name="Matches Drawn")
    lost = models.IntegerField(default=0, verbose_name="Matches Lost")
    
    goals_for = models.IntegerField(default=0, verbose_name="Goals For")
    goals_against = models.IntegerField(default=0, verbose_name="Goals Against")
    goal_difference = models.IntegerField(default=0, verbose_name="Goal Difference")
    points = models.IntegerField(default=0, verbose_name="Points")
    
    position = models.IntegerField(default=1, verbose_name="Position")

    class Meta:
        ordering = ["position", "-points", "-goal_difference", "-goals_for"]
        verbose_name = "Standing"
        verbose_name_plural = "Standings"
        constraints = [
            models.UniqueConstraint(
                fields=["competition", "club"],
                name="unique_club_standing_per_competition",
            )
        ]

    def __str__(self) -> str:
        return f"#{self.position} - {self.club.name} ({self.points} pts) in {self.competition.name}"

    def recalculate_difference(self) -> None:
        self.goal_difference = self.goals_for - self.goals_against
