"""
BOLAYETU — CompetitionRegistration Model

Represents a club's registration in a specific competition/season.
This represents a tenant-scoped N:N relationship between Competition and Club.
"""

from django.db import models
from common.models import BaseModel


class CompetitionRegistration(BaseModel):
    """
    Links a Club to a Competition (season-specific).
    """

    competition = models.ForeignKey(
        "competitions.Competition",
        on_delete=models.CASCADE,
        related_name="registrations",
        verbose_name="Competition",
    )
    club = models.ForeignKey(
        "clubs.Club",
        on_delete=models.CASCADE,
        related_name="competition_registrations",
        verbose_name="Club",
    )
    tenant = models.ForeignKey(
        "core.Tenant",
        on_delete=models.CASCADE,
        related_name="competition_registrations",
        verbose_name="Organization",
    )
    registered_at = models.DateTimeField(auto_now_add=True, verbose_name="Registered At")

    class Meta:
        ordering = ["-registered_at"]
        verbose_name = "Competition Registration"
        verbose_name_plural = "Competition Registrations"
        constraints = [
            models.UniqueConstraint(
                fields=["competition", "club"],
                name="unique_club_per_competition",
            )
        ]

    def __str__(self) -> str:
        return f"{self.club.name} registered in {self.competition.name}"
