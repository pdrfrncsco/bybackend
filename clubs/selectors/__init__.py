"""
BOLAYETU — Clubs Selectors

Read-only queries for the clubs domain.

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

from accounts.models import User
from clubs.constants import ClubStatus, ClubMemberRole
from clubs.models import Club, ClubMember, ClubDocument, ClubSponsor

logger = logging.getLogger(__name__)


class ClubSelector:
    """Read-only queries for Club data."""

    @staticmethod
    def get_by_id(*, club_id: uuid.UUID) -> Optional[Club]:
        """Retrieve a club by its UUID."""
        try:
            return Club.objects.select_related("tenant").get(id=club_id)
        except Club.DoesNotExist:
            return None

    @staticmethod
    def get_by_slug(*, slug: str) -> Optional[Club]:
        """Retrieve a public club by its slug."""
        try:
            return Club.objects.select_related("tenant").get(slug=slug, is_public=True)
        except Club.DoesNotExist:
            return None

    @staticmethod
    def get_by_slug_any(*, slug: str) -> Optional[Club]:
        """Retrieve a club by slug regardless of public status (for admin access)."""
        try:
            return Club.objects.select_related("tenant").get(slug=slug)
        except Club.DoesNotExist:
            return None

    @staticmethod
    def list_public(
        *,
        search: str | None = None,
        tenant_slug: str | None = None,
    ) -> QuerySet:
        """
        Return all public, active clubs.

        Args:
            search: Optional search term for name or city.
            tenant_slug: Optional filter by organization slug.
        """
        queryset = Club.objects.filter(
            is_public=True,
            status=ClubStatus.ACTIVE,
        ).select_related("tenant")

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(city__icontains=search)
            )

        if tenant_slug:
            queryset = queryset.filter(tenant__slug=tenant_slug)

        return queryset.order_by("name")

    @staticmethod
    def list_by_tenant(*, tenant_id: uuid.UUID) -> QuerySet:
        """Return all clubs for a specific tenant (organization)."""
        return Club.objects.filter(tenant_id=tenant_id).select_related("tenant").order_by("name")

    @staticmethod
    def get_squad(*, club: Club) -> QuerySet:
        """
        Return all active players for a club, ordered by shirt number.
        
        NOTE: This method now uses PlayerRegistration instead of ClubMember.
        ClubMember with role="player" is deprecated - use PlayerRegistration instead.
        """
        from players.models import PlayerRegistration
        
        return (
            PlayerRegistration.objects
            .filter(club=club, status__in=["registered", "loaned"])
            .select_related("player")
            .order_by("shirt_number")
        )

    @staticmethod
    def get_staff(*, club: Club) -> QuerySet:
        """
        Return all active staff members for a club, ordered by role.
        """
        return (
            ClubMember.objects
            .filter(club=club, is_active=True)
            .exclude(role=ClubMemberRole.PLAYER)
            .select_related("user")
            .order_by("role")
        )

    @staticmethod
    def get_members(*, club: Club) -> QuerySet:
        """Return all active members for a club."""
        return (
            ClubMember.objects
            .filter(club=club, is_active=True)
            .select_related("user")
            .order_by("role", "-created_at")
        )

    @staticmethod
    def get_member_by_id(*, member_id: uuid.UUID) -> Optional[ClubMember]:
        """Retrieve a club member by ID."""
        try:
            return ClubMember.objects.select_related("club", "user").get(id=member_id)
        except ClubMember.DoesNotExist:
            return None

    @staticmethod
    def is_club_admin(*, user: User, club: Club) -> bool:
        """
        Check if a user has administrative access to a club.

        A user is a club admin if:
            1. They are an admin/owner of the club's tenant (organization), OR
            2. They have an active MANAGER or PRESIDENT role in the club.
        """
        from accounts.constants import MembershipRole
        from accounts.models import TenantMembership

        # Check tenant admin
        is_tenant_admin = TenantMembership.objects.filter(
            user=user,
            tenant=club.tenant,
            is_active=True,
            role__in=MembershipRole.ADMIN_ROLES,
        ).exists()

        if is_tenant_admin:
            return True

        # Check club admin
        return ClubMember.objects.filter(
            user=user,
            club=club,
            is_active=True,
            role__in=ClubMemberRole.ADMIN_ROLES,
        ).exists()

    @staticmethod
    def get_kpis(*, club: Club) -> dict:
        """
        Retrieve KPI statistics for a club.
        """
        squad_count = ClubSelector.get_squad(club=club).count()
        staff_count = ClubSelector.get_staff(club=club).count()

        from competitions.constants import CompetitionStatus
        from competitions.models import Competition, Match

        club_matches = (
            Match.objects.filter(tenant=club.tenant)
            .filter(Q(home_club=club) | Q(away_club=club))
            .select_related("competition", "home_club", "away_club")
        )

        finished_matches = club_matches.filter(status=Match.MatchStatus.FINISHED)
        total_matches = club_matches.count()
        wins = draws = losses = 0
        goals_for = goals_against = 0
        clean_sheets = 0

        for match in finished_matches:
            if match.home_club_id == club.id:
                club_goals = match.home_score or 0
                opponent_goals = match.away_score or 0
            else:
                club_goals = match.away_score or 0
                opponent_goals = match.home_score or 0

            goals_for += club_goals
            goals_against += opponent_goals

            if club_goals > opponent_goals:
                wins += 1
            elif club_goals == opponent_goals:
                draws += 1
            else:
                losses += 1

            if opponent_goals == 0:
                clean_sheets += 1

        active_competitions = (
            Competition.objects.filter(tenant=club.tenant, status=CompetitionStatus.ACTIVE)
            .filter(Q(matches__home_club=club) | Q(matches__away_club=club) | Q(standings__club=club))
            .distinct()
            .count()
        )

        return {
            "squad_size": squad_count,
            "staff_count": staff_count,
            "total_matches": total_matches,
            "wins": wins,
            "draws": draws,
            "losses": losses,
            "goals_for": goals_for,
            "goals_against": goals_against,
            "clean_sheets": clean_sheets,
            "active_competitions": active_competitions,
        }

    @staticmethod
    def get_documents(*, club: Club) -> QuerySet:
        return ClubDocument.objects.filter(club=club).select_related("asset", "uploaded_by")

    @staticmethod
    def get_public_documents(*, club: Club) -> QuerySet:
        return ClubDocument.objects.filter(club=club, is_public=True).select_related("asset")

    @staticmethod
    def get_sponsors(*, club: Club) -> QuerySet:
        return ClubSponsor.objects.filter(club=club).select_related("logo_asset", "uploaded_by")

    @staticmethod
    def get_public_sponsors(*, club: Club) -> QuerySet:
        return ClubSponsor.objects.filter(club=club, is_active=True).select_related("logo_asset")

    @staticmethod
    def count_for_tenant(*, tenant_id: uuid.UUID) -> int:
        """Count active clubs for a tenant."""
        return Club.objects.filter(
            tenant_id=tenant_id,
            status=ClubStatus.ACTIVE,
        ).count()
