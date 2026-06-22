"""
BOLAYETU — Common Base Classes
Skills: BOLAYETU_ARCHITECTURE, BOLAYETU_BACKEND_SKILL

BaseService  — enforces Service Layer pattern
BaseSelector — enforces Selector/Query pattern

Rules:
- ALL business logic lives in Services
- ALL database reads live in Selectors
- Views ONLY orchestrate (call service, return response)
- NEVER bypass: always use selectors for reads, services for writes
"""

import logging
from django.db import transaction

logger = logging.getLogger('bolayetu')


class BaseService:
    """
    Abstract base for all Bolayetu service classes.

    Every service MUST:
    - Accept the requesting user (for permission checks)
    - Accept the current tenant (for isolation)
    - Use @transaction.atomic for writes
    - Raise domain exceptions (from common.exceptions)

    Example:
        class ClubService(BaseService):
            def create_club(self, *, data: dict) -> Club:
                # validate tenant ownership
                # create the object
                # emit signals/tasks
                return club
    """

    def __init__(self, *, user=None, tenant=None):
        """
        Args:
            user:   The authenticated requesting User. Used for ownership validation.
            tenant: The current Tenant (from request.tenant). All operations
                    are scoped to this tenant.
        """
        self.user = user
        self.tenant = tenant

    def _assert_tenant(self):
        """Raise if no tenant is set. Call at start of tenant-scoped methods."""
        if self.tenant is None:
            from common.exceptions import TenantNotFoundException
            raise TenantNotFoundException()

    def _assert_user(self):
        """Raise if no user is set."""
        if self.user is None:
            from rest_framework.exceptions import NotAuthenticated
            raise NotAuthenticated()

    @staticmethod
    def atomic(func):
        """Decorator: wraps a service method in a database transaction."""
        def wrapper(*args, **kwargs):
            with transaction.atomic():
                return func(*args, **kwargs)
        return wrapper


class BaseSelector:
    """
    Abstract base for all Bolayetu selector classes.

    Every selector MUST:
    - Accept the current tenant for query scoping
    - Return QuerySets (not lists) for lazy evaluation
    - Never modify data (read-only pattern)
    - Use select_related/prefetch_related aggressively

    Example:
        class ClubSelector(BaseSelector):
            def get_clubs_list(self, *, filters=None):
                qs = Club.objects.filter(tenant=self.tenant)
                if filters:
                    qs = ClubFilter(filters, queryset=qs).qs
                return qs.select_related('stadium', 'tenant')
    """

    def __init__(self, *, tenant=None, user=None):
        """
        Args:
            tenant: The current Tenant. ALL queries must be scoped to this tenant.
            user:   Optional — for user-specific queries (e.g. favourites).
        """
        self.tenant = tenant
        self.user = user

    def _assert_tenant(self):
        """Raise if no tenant is set."""
        if self.tenant is None:
            from common.exceptions import TenantNotFoundException
            raise TenantNotFoundException()

    def _base_qs(self, model):
        """
        Returns the base tenant-scoped queryset for a model.
        Use this as the starting point for ALL selector queries.

        Usage:
            qs = self._base_qs(Club)
        """
        self._assert_tenant()
        return model.objects.filter(tenant=self.tenant)
