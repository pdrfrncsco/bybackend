"""
BOLAYETU — Organizations Selectors

Read-only queries for the organizations domain.

RULES:
    - Selectors NEVER modify data.
    - All database reads go through selectors.
    - Views and services import from here for queries.
    - Use select_related/prefetch_related to avoid N+1 queries.
"""

import uuid
import logging
from typing import Optional

from django.db.models import QuerySet, Count, Q

from accounts.constants import MembershipRole
from accounts.models import User, TenantMembership
from core.models import Tenant
from organizations.models import OrganizationSubscription

logger = logging.getLogger(__name__)


class OrganizationSelector:
    """Read-only queries for Organization (Tenant) data."""

    @staticmethod
    def get_by_id(*, tenant_id: uuid.UUID) -> Optional[Tenant]:
        """
        Retrieve an organization by its UUID.

        Returns:
            Tenant instance or None if not found.
        """
        try:
            return Tenant.objects.get(id=tenant_id)
        except Tenant.DoesNotExist:
            return None

    @staticmethod
    def get_by_slug(*, slug: str) -> Optional[Tenant]:
        """
        Retrieve a public organization by its slug.

        Returns:
            Tenant instance or None if not found.
        """
        try:
            return Tenant.objects.get(slug=slug, is_public=True)
        except Tenant.DoesNotExist:
            return None

    @staticmethod
    def get_for_user(*, user: User) -> Optional[Tenant]:
        """
        Retrieve the primary organization for an authenticated user.

        Returns the tenant where the user has an active admin/owner membership.
        Falls back to the first active membership if no admin role is found.

        Args:
            user: The authenticated User instance.

        Returns:
            Tenant instance or None if the user has no organization membership.
        """
        admin_membership = (
            TenantMembership.objects
            .filter(
                user=user,
                is_active=True,
                role__in=MembershipRole.ADMIN_ROLES,
            )
            .select_related("tenant")
            .first()
        )

        if admin_membership:
            return admin_membership.tenant

        # Fallback: first active membership
        first_membership = (
            TenantMembership.objects
            .filter(user=user, is_active=True)
            .select_related("tenant")
            .first()
        )

        return first_membership.tenant if first_membership else None

    @staticmethod
    def list_public(*, search: str | None = None, org_type: str | None = None) -> QuerySet:
        """
        Return all public, active organizations.

        Args:
            search: Optional search term for name or description.
            org_type: Optional filter by organization type.

        Returns:
            QuerySet of Tenant instances.
        """
        queryset = Tenant.objects.filter(is_public=True, status=Tenant.TenantStatus.ACTIVE)

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )

        if org_type:
            queryset = queryset.filter(type=org_type)

        return queryset.order_by("name")

    @staticmethod
    def get_subscription(*, user: User, tenant: Tenant) -> Optional[OrganizationSubscription]:
        """
        Retrieve the subscription record for a user and organization.

        Returns:
            OrganizationSubscription or None.
        """
        try:
            return OrganizationSubscription.objects.get(user=user, tenant=tenant)
        except OrganizationSubscription.DoesNotExist:
            return None

    @staticmethod
    def is_subscribed(*, user: User, tenant: Tenant) -> bool:
        """
        Check if a user has an active subscription to an organization.

        Returns:
            True if the user is an active subscriber.
        """
        return OrganizationSubscription.objects.filter(
            user=user,
            tenant=tenant,
            is_active=True,
        ).exists()

    @staticmethod
    def count_subscribers(*, tenant: Tenant) -> int:
        """
        Count active subscribers for an organization.

        Returns:
            Number of active subscriptions.
        """
        return OrganizationSubscription.objects.filter(
            tenant=tenant,
            is_active=True,
        ).count()

    @staticmethod
    def get_kpis(*, tenant: Tenant) -> dict:
        """
        Retrieve KPI statistics for an organization.

        Returns placeholder data for now — will be populated when
        competitions, matches, and statistics modules are implemented.

        Args:
            tenant: The Tenant instance.

        Returns:
            Dictionary of KPI values.
        """
        subscriber_count = OrganizationSelector.count_subscribers(tenant=tenant)

        return {
            "total_games": 0,
            "total_goals": 0,
            "goals_per_game": 0.0,
            "live_games": 0,
            "scheduled_games": 0,
            "active_subscribers": subscriber_count,
            "total_tournaments": 0,
            "active_tournaments": 0,
            "upcoming_tournaments": 0,
            "completed_tournaments": 0,
            "total_clubs": 0,
        }

    @staticmethod
    def get_history(*, tenant: Tenant) -> list:
        """
        Retrieve tournament history for an organization.

        Returns an empty list for now — will be populated when
        the competitions module is implemented.

        Args:
            tenant: The Tenant instance.

        Returns:
            List of history entries.
        """
        return []

    @staticmethod
    def get_tournaments(*, tenant: Tenant) -> list:
        """
        Retrieve tournaments for an organization.

        Returns an empty list for now — will be populated when
        the competitions module is implemented.

        Returns:
            List of tournament data.
        """
        return []

    @staticmethod
    def get_clubs(*, tenant: Tenant) -> list:
        """
        Retrieve clubs affiliated with an organization.

        Returns an empty list for now — will be populated when
        the clubs module is implemented.

        Returns:
            List of club data.
        """
        return []
