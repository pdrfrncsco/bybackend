"""MatchCenter-specific RBAC permissions."""

from rest_framework.permissions import BasePermission

from accounts.constants import AccountStatus, MembershipRole
from accounts.models import TenantMembership
from clubs.models import ClubMember


class IsMatchEventOperator(BasePermission):
    """Allow active organization admins/managers to operate the live feed."""

    message = "You must be an active match operator to record live events."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.status == AccountStatus.ACTIVE
            and TenantMembership.objects.filter(
                user=user,
                is_active=True,
                role__in=[*MembershipRole.ADMIN_ROLES, MembershipRole.MANAGER],
            ).exists()
        )


class IsMatchReportOperator(IsMatchEventOperator):
    """Allow operators to submit match data; approval remains administrative."""

    message = "You must be an active match report operator."


class CanManageClubLineup(BasePermission):
    """Authorize lineup mutations for a specific club and match.

    This is deliberately tenant-aware: an organization administrator must be
    an administrator of the request tenant, not merely an administrator of a
    different tenant owned by the same user.
    """

    message = "You are not authorized to manage this club's lineup."
    # The club affiliation workflow assigns its owner as president.
    # Keep this list aligned with ClubService.assert_is_club_admin().
    CLUB_ROLES = ("president", "manager", "coach", "assistant_coach")

    @classmethod
    def user_can_manage(cls, *, user, tenant, match, club) -> bool:
        if not user or not user.is_authenticated:
            return False
        if getattr(user, "status", None) != AccountStatus.ACTIVE:
            return False
        if club.tenant_id != tenant.id or match.tenant_id != tenant.id:
            return False
        if str(club.id) not in {str(match.home_club_id), str(match.away_club_id)}:
            return False
        if user.is_superuser:
            return True

        if TenantMembership.objects.filter(
            user=user,
            tenant=tenant,
            is_active=True,
            role__in=MembershipRole.ADMIN_ROLES,
        ).exists():
            return True

        return ClubMember.objects.filter(
            user=user,
            club=club,
            is_active=True,
            role__in=cls.CLUB_ROLES,
        ).exists()

    def has_permission(self, request, view):
        """Support direct DRF use when the request carries match and club IDs."""
        club_id = request.data.get("club_id")
        match_id = view.kwargs.get("match_id")
        if not club_id or not match_id:
            return False

        from clubs.models import Club
        from competitions.models import Match

        tenant = getattr(request, "tenant", None)
        if tenant is None:
            tenant_id = request.headers.get("X-Tenant-ID")
            if tenant_id:
                from core.models import Tenant
                tenant = Tenant.objects.filter(id=tenant_id).first()
        if tenant is None:
            return False

        match = Match.objects.filter(id=match_id).first()
        club = Club.objects.filter(id=club_id).first()
        return bool(match and club and self.user_can_manage(user=request.user, tenant=tenant, match=match, club=club))
