"""
BOLAYETU — Competition Model

Represents a competition (league, tournament, or cup) within a tenant.
"""

from django.db import models
from django.utils.text import slugify

from common.models import BaseModel
from competitions.constants import CompetitionType, CompetitionStatus


class Competition(BaseModel):
    """
    A competition organized by a tenant (organization).

    Examples:
        - Girabola (league)
        - Taça de Angola (cup)
        - Torneio Provincial de Luanda (tournament)
    """

    name = models.CharField(max_length=255, verbose_name="Name")
    slug = models.SlugField(max_length=255, blank=True, verbose_name="Slug")
    tenant = models.ForeignKey(
        "core.Tenant",
        on_delete=models.CASCADE,
        related_name="competitions",
        verbose_name="Organization",
    )
    competition_type = models.CharField(
        max_length=20,
        choices=CompetitionType.CHOICES,
        default=CompetitionType.LEAGUE,
        verbose_name="Type",
    )
    season = models.CharField(
        max_length=20,
        verbose_name="Season",
        help_text="e.g. 2025/26",
    )
    status = models.CharField(
        max_length=20,
        choices=CompetitionStatus.CHOICES,
        default=CompetitionStatus.DRAFT,
        verbose_name="Status",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Competition"
        verbose_name_plural = "Competitions"
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "slug", "season"],
                name="unique_competition_per_tenant_season",
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.season})"

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            base = slugify(self.name) or "competition"
            self.slug = base
        super().save(*args, **kwargs)
