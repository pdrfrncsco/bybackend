"""
BOLAYETU — Club Model

Represents a football club within the Bolayetu platform.

A Club belongs to a Tenant (organization). It is the primary entity
that connects players, staff, competitions, and fans.

Architecture:
    - Club is a TENANT-SCOPED entity — every club belongs to exactly one Tenant.
    - Players and staff are linked to clubs via ClubMember.
    - Clubs participate in competitions organized by tenants.
"""

from django.db import models
from django.utils.text import slugify

from common.models import BaseModel


class Club(BaseModel):
    """
    Represents a football club in the Bolayetu ecosystem.

    Each club is affiliated with a Tenant (organization) and has its own
    branding, stadium, and contact information.

    Examples:
        - Petro de Luanda (FAF)
        - 1º de Agosto (FAF)
        - Sagrada Esperança (FAF)
    """

    # Identity
    name = models.CharField(max_length=255, verbose_name="Name")
    slug = models.SlugField(max_length=255, blank=True, verbose_name="Slug")
    short_name = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="Short Name",
        help_text="Abbreviated name for tables and fixtures (e.g. 'PLU', '1º AGO').",
    )

    # Tenant ownership
    tenant = models.ForeignKey(
        "core.Tenant",
        on_delete=models.CASCADE,
        related_name="clubs",
        verbose_name="Organization",
    )

    # Branding
    logo = models.ImageField(
        upload_to="club-logos/",
        max_length=500,
        null=True,
        blank=True,
        verbose_name="Logo",
        help_text="Club logo file (stored in configured DEFAULT_FILE_STORAGE).",
    )
    primary_color = models.CharField(
        max_length=7, default="#014D40", verbose_name="Primary Color"
    )
    secondary_color = models.CharField(
        max_length=7, default="#94D3C1", verbose_name="Secondary Color"
    )

    # Foundation
    founded_year = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Founded Year",
    )

    # Stadium
    stadium_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Stadium Name",
    )
    stadium_capacity = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Stadium Capacity",
    )

    # Location
    country = models.CharField(max_length=100, default="Angola", verbose_name="Country")
    city = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="City",
    )

    # Contact
    email = models.EmailField(null=True, blank=True, verbose_name="Email")
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name="Phone")
    website = models.URLField(null=True, blank=True, verbose_name="Website")

    # Description
    description = models.TextField(null=True, blank=True, verbose_name="Description")

    # Status
    is_public = models.BooleanField(default=True, verbose_name="Is Public")
    is_verified = models.BooleanField(default=False, verbose_name="Is Verified")
    status = models.CharField(
        max_length=20,
        choices=[
            ("active", "Ativo"),
            ("suspended", "Suspenso"),
            ("inactive", "Inativo"),
        ],
        default="active",
        verbose_name="Status",
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Club"
        verbose_name_plural = "Clubs"
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "name"],
                name="unique_club_name_per_tenant",
            ),
            models.UniqueConstraint(
                fields=["tenant", "slug"],
                name="unique_club_slug_per_tenant",
            ),
        ]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            base = slugify(self.name)
            slug = base
            counter = 1
            while Club.objects.filter(tenant=self.tenant, slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def is_active(self) -> bool:
        """Returns True if the club is currently active."""
        return self.status == "active"

    @property
    def location(self) -> str:
        """Returns a combined location string."""
        parts = [p for p in [self.city, self.country] if p]
        return ", ".join(parts)
