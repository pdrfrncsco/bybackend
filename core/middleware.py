"""
BOLAYETU — Core Middleware
Skills: BOLAYETU_MULTITENANT_SKILL, BOLAYETU_SECURITY_SKILL

TenantMiddleware:
- Resolves request.tenant from subdomain on every request
- girabola.bolayetu.com → Tenant(slug='girabola')
- app.bolayetu.com / api.bolayetu.com → request.tenant = None (platform level)
- NEVER exposes data across tenants

AuthTrackingMiddleware:
- Logs all authenticated API access for audit trail
"""

import logging
from django.conf import settings
from django.core.cache import cache

from core.models import Tenant

logger = logging.getLogger('bolayetu')
access_logger = logging.getLogger('access')

# ===================================================================
# TENANT MIDDLEWARE
# Skill: BOLAYETU_MULTITENANT_SKILL
#
# Every request gets request.tenant resolved.
# All downstream services MUST use request.tenant to scope queries.
# NEVER return data from a different tenant.
# ===================================================================

class TenantMiddleware:
    """
    Resolves the current tenant from the HTTP Host header subdomain.

    Examples:
        girabola.bolayetu.com  → Tenant(slug='girabola')
        faf.bolayetu.com       → Tenant(slug='faf')
        app.bolayetu.com       → None (platform level)
        localhost              → None (local dev, no tenant)

    Sets on request:
        request.tenant         → Tenant instance or None
        request.tenant_slug    → str or None
    """

    CACHE_TTL = 300  # 5 minutes
    CACHE_KEY_PREFIX = 'tenant_middleware:'

    def __init__(self, get_response):
        self.get_response = get_response
        self.domain = getattr(settings, 'BOLAYETU_DOMAIN', 'bolayetu.com')
        self.reserved = getattr(
            settings,
            'BOLAYETU_RESERVED_SUBDOMAINS',
            ['www', 'app', 'api', 'admin', 'cdn', 'mail', 'smtp', 'ftp', 'status']
        )

    def __call__(self, request):
        request.tenant = None
        request.tenant_slug = None

        slug = self._extract_slug(request)

        if slug:
            request.tenant_slug = slug
            request.tenant = self._resolve_tenant(slug)

            if request.tenant is None:
                logger.warning(
                    'TenantMiddleware: unknown slug=%s host=%s',
                    slug,
                    request.get_host()
                )

        return self.get_response(request)

    def _extract_slug(self, request) -> str | None:
        """
        Extract tenant slug from Host header.

        girabola.bolayetu.com → 'girabola'
        bolayetu.com          → None
        localhost             → None
        """
        host = request.get_host().lower()

        # Strip port if present
        if ':' in host:
            host = host.split(':')[0]

        # Only process if host ends with our domain
        if host == self.domain or not host.endswith(f'.{self.domain}'):
            return None

        # Extract subdomain
        subdomain = host[: -(len(self.domain) + 1)]  # Remove .bolayetu.com

        # Multi-level subdomains (e.g. test.girabola.bolayetu.com) — take last part
        parts = subdomain.split('.')
        slug = parts[-1] if parts else subdomain

        if slug in self.reserved:
            return None

        return slug or None

    def _resolve_tenant(self, slug: str) -> Tenant | None:
        """
        Resolve Tenant by slug, with Redis caching.
        Cache key: tenant_middleware:girabola
        """
        cache_key = f'{self.CACHE_KEY_PREFIX}{slug}'

        # Try cache first
        cached = cache.get(cache_key)
        if cached is not None:
            # Cache stores False for "not found", Tenant object otherwise
            return cached if cached is not False else None

        # Hit database
        try:
            tenant = (
                Tenant.objects
                .select_related()
                .get(slug=slug, is_active=True)
            )
            cache.set(cache_key, tenant, self.CACHE_TTL)
            return tenant
        except Tenant.DoesNotExist:
            # Cache negative result to avoid repeated DB hits
            cache.set(cache_key, False, self.CACHE_TTL)
            return None

    @staticmethod
    def invalidate_cache(slug: str) -> None:
        """
        Call this when a Tenant is updated/deactivated
        to immediately clear the middleware cache.
        """
        cache.delete(f'{TenantMiddleware.CACHE_KEY_PREFIX}{slug}')


# ===================================================================
# AUTH TRACKING MIDDLEWARE
# Logs all API access for security audit trail
# ===================================================================

class AuthTrackingMiddleware:
    """
    Logs every /api/ request with user, tenant, method, status.
    Supports the AdminActionLog audit requirement.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        is_authenticated = bool(getattr(user, 'is_authenticated', False))
        setattr(request, 'is_authenticated_user', is_authenticated)

        response = self.get_response(request)

        path = getattr(request, 'path', '')
        if path.startswith('/api/'):
            try:
                tenant = getattr(request, 'tenant', None)
                access_logger.info(
                    'access path=%s method=%s status=%s user_id=%s tenant=%s ip=%s',
                    path,
                    request.method,
                    getattr(response, 'status_code', ''),
                    getattr(user, 'id', None),
                    getattr(tenant, 'slug', None),
                    self._get_client_ip(request),
                )
            except Exception:
                pass

        return response

    @staticmethod
    def _get_client_ip(request) -> str:
        """Extract real client IP, respecting Cloudflare proxy headers."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        cf_connecting_ip = request.META.get('HTTP_CF_CONNECTING_IP')
        if cf_connecting_ip:
            return cf_connecting_ip
        return request.META.get('REMOTE_ADDR', '')
