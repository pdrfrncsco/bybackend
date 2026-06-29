"""
BOLAYETU — Accounts Selectors

Read-only queries for the accounts domain.

RULES:
    - Selectors NEVER modify data.
    - All database reads go through selectors.
    - Views and services import from here for queries.
    - Use select_related/prefetch_related to avoid N+1 queries.
"""

import uuid
import logging
from typing import Optional

from django.db.models import QuerySet

from accounts.models import User, TenantMembership

logger = logging.getLogger(__name__)


class UserSelector:
    """Read-only queries for the User model."""

    @staticmethod
    def get_by_id(*, user_id: uuid.UUID) -> Optional[User]:
        """
        Retrieve a user by their UUID.

        Returns:
            User instance or None if not found.
        """
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @staticmethod
    def get_by_email(*, email: str) -> Optional[User]:
        """
        Retrieve a user by email address (case-insensitive).

        Returns:
            User instance or None if not found.
        """
        try:
            return User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return None

    @staticmethod
    def email_exists(*, email: str) -> bool:
        """
        Check if an email address is already registered.

        Returns:
            True if the email is taken, False otherwise.
        """
        return User.objects.filter(email__iexact=email).exists()

    @staticmethod
    def list_all() -> QuerySet:
        """
        Return all users ordered by creation date (newest first).

        Returns:
            QuerySet of User instances.
        """
        return User.objects.all()

    @staticmethod
    def list_active() -> QuerySet:
        """
        Return all users with ACTIVE account status.

        Returns:
            QuerySet of active User instances.
        """
        from accounts.constants import AccountStatus
        return User.objects.filter(status=AccountStatus.ACTIVE)

    @staticmethod
    def get_memberships_for_user(*, user: User) -> QuerySet:
        """
        Return all active tenant memberships for a user.

        Returns:
            QuerySet of TenantMembership instances with tenant preloaded.
        """
        return (
            TenantMembership.objects
            .filter(user=user, is_active=True)
            .select_related("tenant")
            .order_by("-joined_at")
        )


class TenantMembershipSelector:
    """Read-only queries for TenantMembership."""

    @staticmethod
    def get_membership(*, user: User, tenant_id: uuid.UUID) -> Optional[TenantMembership]:
        """
        Retrieve the membership record for a user in a specific tenant.

        Returns:
            TenantMembership or None.
        """
        try:
            return TenantMembership.objects.select_related("user", "tenant").get(
                user=user,
                tenant_id=tenant_id,
            )
        except TenantMembership.DoesNotExist:
            return None

    @staticmethod
    def user_belongs_to_tenant(*, user: User, tenant_id: uuid.UUID) -> bool:
        """
        Check if a user has an active membership in a tenant.

        Returns:
            True if the user is an active member.
        """
        return TenantMembership.objects.filter(
            user=user,
            tenant_id=tenant_id,
            is_active=True,
        ).exists()

    @staticmethod
    def list_tenant_members(*, tenant_id: uuid.UUID) -> QuerySet:
        """
        Return all active members of a tenant.

        Returns:
            QuerySet of TenantMembership with user preloaded.
        """
        return (
            TenantMembership.objects
            .filter(tenant_id=tenant_id, is_active=True)
            .select_related("user")
            .order_by("user__first_name", "user__last_name")
        )
