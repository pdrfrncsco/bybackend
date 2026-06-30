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
            return Tenant.objects.get(
                slug=slug,
                is_public=True,
                status=Tenant.TenantStatus.ACTIVE,
            )
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
        """
        from competitions.constants import CompetitionStatus
        from competitions.models import Competition
        from clubs.selectors import ClubSelector

        subscriber_count = OrganizationSelector.count_subscribers(tenant=tenant)
        competitions = Competition.objects.filter(tenant=tenant)
        total_tournaments = competitions.count()
        active_tournaments = competitions.filter(status=CompetitionStatus.ACTIVE).count()
        upcoming_tournaments = competitions.filter(status=CompetitionStatus.DRAFT).count()
        completed_tournaments = competitions.filter(status=CompetitionStatus.COMPLETED).count()
        total_clubs = ClubSelector.count_for_tenant(tenant_id=tenant.id)

        return {
            "total_games": 0,
            "total_goals": 0,
            "goals_per_game": 0.0,
            "live_games": 0,
            "scheduled_games": 0,
            "active_subscribers": subscriber_count,
            "total_tournaments": total_tournaments,
            "active_tournaments": active_tournaments,
            "upcoming_tournaments": upcoming_tournaments,
            "completed_tournaments": completed_tournaments,
            "total_clubs": total_clubs,
        }

    @staticmethod
    def get_history(*, tenant: Tenant) -> list:
        """
        Retrieve tournament history for an organization.

        Returns completed competitions until match history is implemented.
        """
        from competitions.constants import CompetitionStatus
        from competitions.models import Competition

        competitions = Competition.objects.filter(
            tenant=tenant,
            status=CompetitionStatus.COMPLETED,
        ).order_by("-season", "name")

        return [
            {
                "season": comp.season,
                "tournament_name": comp.name,
                "tournament_id": str(comp.id),
                "tournament_format": comp.competition_type,
                "winner_club_name": "",
                "runner_up_club_name": "",
                "winner_club_id": "",
                "runner_up_club_id": "",
            }
            for comp in competitions
        ]

    @staticmethod
    def get_tournaments(*, tenant: Tenant) -> list:
        """
        Retrieve competitions for an organization.
        """
        from competitions.selectors import CompetitionSelector
        from competitions.serializers import CompetitionSerializer

        competitions = CompetitionSelector.list_for_tenant(tenant=tenant)
        return CompetitionSerializer(competitions, many=True).data

    @staticmethod
    def get_clubs(*, tenant: Tenant) -> list:
        """
        Retrieve public clubs affiliated with an organization.
        """
        from clubs.selectors import ClubSelector
        from clubs.serializers import PublicClubSerializer

        clubs = ClubSelector.list_by_tenant(tenant_id=tenant.id).filter(is_public=True)
        return PublicClubSerializer(clubs, many=True).data
