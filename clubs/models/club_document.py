"""
BOLAYETU — Club Document Model

Represents a document uploaded for a club and stored via the DAM.
"""

from django.conf import settings
from django.db import models

from common.models import BaseModel


class ClubDocument(BaseModel):
    class Category(models.TextChoices):
        CONTRACT = "contract", "Contrato"
        CERTIFICATE = "certificate", "Certificado"
        LICENSE = "license", "Licença"
        REGULATION = "regulation", "Regulamento"
        OTHER = "other", "Outro"

    club = models.ForeignKey(
        "clubs.Club",
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name="Club",
    )
    tenant = models.ForeignKey(
        "core.Tenant",
        on_delete=models.CASCADE,
        related_name="club_documents",
        verbose_name="Organization",
    )
    title = models.CharField(max_length=255, verbose_name="Title")
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.OTHER,
        verbose_name="Category",
    )
    description = models.TextField(blank=True, default="", verbose_name="Description")
    asset = models.ForeignKey(
        "media_assets.MediaAsset",
        on_delete=models.CASCADE,
        related_name="club_documents",
        verbose_name="Asset",
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="club_documents_uploaded",
        verbose_name="Uploaded By",
    )
    is_public = models.BooleanField(default=False, verbose_name="Is Public")
    valid_until = models.DateField(null=True, blank=True, verbose_name="Valid Until")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Club Document"
        verbose_name_plural = "Club Documents"
        constraints = [
            models.UniqueConstraint(
                fields=["club", "title"],
                name="unique_club_document_title_per_club",
            )
        ]

    def __str__(self) -> str:
        return f"{self.title} — {self.club.name}"
