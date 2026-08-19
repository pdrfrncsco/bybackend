"""MatchCenter-specific RBAC permissions."""

from rest_framework.permissions import BasePermission

from accounts.constants import AccountStatus, MembershipRole
from accounts.models import TenantMembership


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
