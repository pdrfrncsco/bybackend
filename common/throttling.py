"""
BOLAYETU — Common Throttling
Tenant-aware rate limiters.
Skill: BOLAYETU_SECURITY_SKILL
"""

from rest_framework.throttling import BaseThrottle, UserRateThrottle


class TenantRateThrottle(UserRateThrottle):
    """
    Rate limiting scoped per tenant.
    Prevents one tenant from starving resources for others.
    """
    scope = 'tenant'

    def get_cache_key(self, request, view):
        tenant = getattr(request, 'tenant', None)
        if tenant is None:
            return None
        return self.cache_format % {
            'scope': self.scope,
            'ident': str(tenant.id),
        }
