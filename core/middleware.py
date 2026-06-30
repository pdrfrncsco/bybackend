from django.utils.deprecation import MiddlewareMixin

from core.models import Tenant


class TenantMiddleware(MiddlewareMixin):
    """Resolve tenant by subdomain and attach to request. """

    def process_request(self, request):
        host = request.get_host().split(":")[0]
        parts = host.split(".")
        # Expect subdomain.domain.tld (e.g. faf.bolayetu.com)
        if len(parts) < 3:
            request.tenant = None
            return

        subdomain = parts[0].lower()
        try:
            tenant = Tenant.objects.filter(subdomain=subdomain).first()
        except Exception:
            tenant = None

        request.tenant = tenant