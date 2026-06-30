"""
BOLAYETU — Core Models

Defines the Tenant model — the foundation of the multi-tenant architecture.

Every organization that uses the Bolayetu platform is a Tenant.
All tenant-scoped data (competitions, clubs, matches) references this model.

Architecture note:
    Tenant is a TENANT-domain entity.
    User and Player are GLOBAL-domain entities and do NOT belong to a Tenant.
    See: 06A_GLOBAL_AND_TENANT_DOMAIN.md
"""

from django.db import models
from django.utils.text import slugify

from common.models import BaseModel


class Tenant(BaseModel):
    """
    Represents an independent organization within the Bolayetu platform.

    Each Tenant has isolated data, independent branding, and its own
    configurations. Tenants are identified by their subdomain.

    Examples:
        - Federação Angolana de Futebol (FAF) → faf.bolayetu.com
        - Associação Provincial de Futebol de Luanda → apfl.bolayetu.com
        - Girabola → girabola.bolayetu.com
    """

    class TenantType(models.TextChoices):
        FEDERATION = "federation", "Federação"
        ASSOCIATION = "association", "Associação"
        LEAGUE = "league", "Liga"
        ORGANIZER = "organizer", "Organizador"
        ACADEMY = "academy", "Academia"
        CLUB = "club", "Clube"
        PLAYER = "player", "Jogador"

    class TenantStatus(models.TextChoices):
        PENDING = "pending", "Pendente"
        ACTIVE = "active", "Ativa"
        SUSPENDED = "suspended", "Suspensa"
        CLOSED = "closed", "Encerrada"

    # Identity
    name = models.CharField(max_length=255, unique=True, verbose_name="Name")
    slug = models.SlugField(max_length=255, unique=True, blank=True, verbose_name="Slug")
    type = models.CharField(
        max_length=20,
        choices=TenantType.choices,
        default=TenantType.FEDERATION,
        verbose_name="Type",
    )

    # Multi-tenant routing
    subdomain = models.CharField(
        max_length=63,
        unique=True,
        null=True,
        blank=True,
        verbose_name="Subdomain",
        help_text="e.g. 'faf' for faf.bolayetu.com",
    )

    # Branding
    logo = models.ImageField(
        upload_to="logos/",
        max_length=500,
        null=True,
        blank=True,
        verbose_name="Logo",
        help_text="Organization logo file (stored in configured DEFAULT_FILE_STORAGE).",
    )
    banner = models.ImageField(
        upload_to="banners/",
        max_length=500,
        null=True,
        blank=True,
        verbose_name="Banner",
        help_text="Organization banner file (stored in configured DEFAULT_FILE_STORAGE).",
    )
    primary_color = models.CharField(max_length=7, default="#014D40", verbose_name="Primary Color")
    secondary_color = models.CharField(max_length=7, default="#94D3C1", verbose_name="Secondary Color")

    # Contact
    email = models.EmailField(null=True, blank=True, verbose_name="Email")
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name="Phone")
    website = models.URLField(null=True, blank=True, verbose_name="Website")

    # Location
    country = models.CharField(max_length=100, default="Angola", verbose_name="Country")
    city = models.CharField(max_length=255, null=True, blank=True, verbose_name="City")

    # Description
    description = models.TextField(null=True, blank=True, verbose_name="Description")

    # Settings
    language = models.CharField(max_length=5, default="pt", verbose_name="Language")
    timezone = models.CharField(max_length=50, default="Africa/Luanda", verbose_name="Timezone")

    # Status
    status = models.CharField(
        max_length=20,
        choices=TenantStatus.choices,
        default=TenantStatus.PENDING,
        verbose_name="Status",
    )
    is_public = models.BooleanField(default=True, verbose_name="Is Public")
    is_verified = models.BooleanField(default=False, verbose_name="Is Verified")

    class Meta:
        ordering = ["name"]
        verbose_name = "Tenant"
        verbose_name_plural = "Tenants"

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def is_active(self) -> bool:
        """Returns True if the tenant is currently active."""
        return self.status == self.TenantStatus.ACTIVE

    @property
    def domain(self) -> str | None:
        """Returns the full subdomain URL for this tenant."""
        if self.subdomain:
            return f"{self.subdomain}.bolayetu.com"
        return None
