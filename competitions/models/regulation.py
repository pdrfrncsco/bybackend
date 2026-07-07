"""
BOLAYETU — Competition Regulation Model

Represents an official regulation document for a competition.
The regulation document itself is stored in the DAM and linked via MediaUsage.
"""

from django.conf import settings
from django.db import models

from common.models import BaseModel


class CompetitionRegulation(BaseModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Rascunho"
        PUBLISHED = "published", "Publicado"
        ARCHIVED = "archived", "Arquivado"

    competition = models.ForeignKey(
        "competitions.Competition",
        on_delete=models.CASCADE,
        related_name="regulations",
        verbose_name="Competition",
    )
    tenant = models.ForeignKey(
        "core.Tenant",
        on_delete=models.CASCADE,
        related_name="competition_regulations",
        verbose_name="Organization",
    )
    title = models.CharField(max_length=255, verbose_name="Title")
    summary = models.TextField(blank=True, default="", verbose_name="Summary")
    version = models.CharField(max_length=32, default="1.0", verbose_name="Version")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name="Status",
    )
    published_at = models.DateTimeField(null=True, blank=True, verbose_name="Published At")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_competition_regulations",
        verbose_name="Uploaded By",
    )

    class Meta:
        ordering = ["-published_at", "-created_at"]
        verbose_name = "Competition Regulation"
        verbose_name_plural = "Competition Regulations"
        constraints = [
            models.UniqueConstraint(
                fields=["competition", "title", "version"],
                name="unique_competition_regulation_version",
            )
        ]

    def __str__(self) -> str:
        return f"{self.competition.name} - {self.title} ({self.version})"
