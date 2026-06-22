"""
BOLAYETU — Core Models
Skills: BOLAYETU_ARCHITECTURE, BOLAYETU_MULTITENANT_SKILL

BaseModel:  UUID PK, timestamps — inherited by all Bolayetu models
Tenant:     Root aggregate — the primary multi-tenant unit
"""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _


class BaseModel(models.Model):
    """
    Abstract base model for all Bolayetu entities.

    Provides:
    - UUID primary key (no sequential IDs exposed)
    - created_at / updated_at timestamps (auto-managed)
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated at'))

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def __repr__(self):
        return f'<{self.__class__.__name__} id={self.id}>'


class Tenant(BaseModel):
    """
    Tenant — the primary multi-tenant unit in Bolayetu.

    Every Tenant is a Football Organization (federation, league, association, etc.)
    All data in the platform is scoped to a Tenant.

    URL pattern: {slug}.bolayetu.com
    Examples:
        faf.bolayetu.com        → FAF (Federação Angolana de Futebol)
        girabola.bolayetu.com   → Girabola
        apf-luanda.bolayetu.com → APF Luanda

    Rules (BOLAYETU_MULTITENANT_SKILL):
    - Every entity must belong to a tenant.
    - Never return records from another tenant.
    - All queries must be tenant-scoped via selectors.
    """

    class OrgType(models.TextChoices):
        FEDERATION = 'federation', _('Federation')
        LEAGUE = 'league', _('League')
        ASSOCIATION = 'association', _('Association')
        TOURNAMENT = 'tournament', _('Tournament organiser')
        SCHOOL = 'school', _('Football School')
        AMATEUR = 'amateur', _('Amateur Organisation')

    # ─── Identity ────────────────────────────────────────────────
    name = models.CharField(max_length=255, verbose_name=_('Name'))
    slug = models.SlugField(
        unique=True,
        verbose_name=_('Slug'),
        help_text=_('Used as subdomain: slug.bolayetu.com'),
    )
    type = models.CharField(
        max_length=20,
        choices=OrgType.choices,
        default=OrgType.LEAGUE,
        verbose_name=_('Type'),
    )

    # ─── Branding ────────────────────────────────────────────────
    primary_color = models.CharField(max_length=7, default='#1B4D3E', verbose_name=_('Primary colour'))
    secondary_color = models.CharField(max_length=7, default='#D4AF37', verbose_name=_('Secondary colour'))
    accent_color = models.CharField(max_length=7, default='#E63946', verbose_name=_('Accent colour'))

    # Logo stored in Cloudflare R2 via infrastructure.storage.r2_storage
    logo = models.ImageField(
        upload_to='tenants/logos/',
        null=True,
        blank=True,
        verbose_name=_('Logo'),
    )

    # ─── Contact ─────────────────────────────────────────────────
    country = models.CharField(max_length=100, blank=True, default='Angola', verbose_name=_('Country'))
    location = models.CharField(max_length=255, blank=True, default='', verbose_name=_('Location'))
    email = models.EmailField(blank=True, default='', verbose_name=_('Email'))
    phone = models.CharField(max_length=50, blank=True, default='', verbose_name=_('Phone'))
    website = models.URLField(blank=True, default='', verbose_name=_('Website'))
    description = models.TextField(blank=True, default='', verbose_name=_('Description'))

    # ─── Status ──────────────────────────────────────────────────
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is active'),
        help_text=_('Inactive tenants are not resolved by TenantMiddleware'),
    )
    is_public = models.BooleanField(
        default=True,
        verbose_name=_('Is public'),
        help_text=_('Public tenants appear on the platform directory'),
    )
    verified = models.BooleanField(
        default=False,
        verbose_name=_('Verified'),
        help_text=_('Verified by Bolayetu platform administrators'),
    )

    class Meta:
        verbose_name = _('Tenant')
        verbose_name_plural = _('Tenants')
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug'], name='tenant_slug_idx'),
            models.Index(fields=['is_active', 'is_public'], name='tenant_status_idx'),
        ]

    def __str__(self):
        return f'{self.name} ({self.slug})'

    @property
    def subdomain_url(self) -> str:
        """Return the full subdomain URL for this tenant."""
        from django.conf import settings
        domain = getattr(settings, 'BOLAYETU_DOMAIN', 'bolayetu.com')
        return f'https://{self.slug}.{domain}'

    @property
    def logo_url(self) -> str | None:
        """Return CDN URL for the tenant logo."""
        if self.logo:
            return self.logo.url
        return None
