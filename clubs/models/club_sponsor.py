"""
BOLAYETU — Club Sponsor Model

Represents a sponsor/partner attached to a club profile.
"""

from django.conf import settings
from django.db import models

from common.models import BaseModel


class ClubSponsor(BaseModel):
    class SponsorType(models.TextChoices):
        MAIN = "main", "Principal"
        OFFICIAL = "official", "Oficial"
        PARTNER = "partner", "Parceiro"
        TECHNICAL = "technical", "Técnico"
        MEDIA = "media", "Media"
        OTHER = "other", "Outro"

    club = models.ForeignKey(
        "clubs.Club",
        on_delete=models.CASCADE,
        related_name="sponsors",
        verbose_name="Club",
    )
    tenant = models.ForeignKey(
        "core.Tenant",
        on_delete=models.CASCADE,
        related_name="club_sponsors",
        verbose_name="Organization",
    )
    name = models.CharField(max_length=255, verbose_name="Name")
    sponsor_type = models.CharField(
        max_length=20,
        choices=SponsorType.choices,
        default=SponsorType.PARTNER,
        verbose_name="Sponsor Type",
    )
    description = models.TextField(blank=True, default="", verbose_name="Description")
    website = models.URLField(null=True, blank=True, verbose_name="Website")
    logo_asset = models.ForeignKey(
        "media_assets.MediaAsset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="club_sponsor_logos",
        verbose_name="Logo Asset",
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="club_sponsors_uploaded",
        verbose_name="Uploaded By",
    )
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    sort_order = models.PositiveIntegerField(default=0, verbose_name="Sort Order")

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "Club Sponsor"
        verbose_name_plural = "Club Sponsors"
        constraints = [
            models.UniqueConstraint(
                fields=["club", "name"],
                name="unique_club_sponsor_name_per_club",
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} — {self.club.name}"
