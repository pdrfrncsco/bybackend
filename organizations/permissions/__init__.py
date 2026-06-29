"""
BOLAYETU — Organizations Permissions

RBAC permission classes for the organizations domain.

Architecture rule:
    Permissions are NEVER checked inside services.
    They are evaluated by DRF at the view level, before the service is called.
"""

from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.views import APIView

from accounts.constants import AccountStatus, MembershipRole
from accounts.selectors import TenantMembershipSelector
from core.models import Tenant


class IsActiveAccount(BasePermission):
    """
    Allow access only to users with an ACTIVE account status.
    """

    message = "Your account is not active. Please contact support."

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.status == AccountStatus.ACTIVE
        )


class IsOrganizationAdmin(BasePermission):
    """
    Allow access only to users who are admins/owners of an organization.

    The organization is resolved from the authenticated user's membership.
    Used for endpoints like /organizations/me/ (PATCH).
    """

    message = "You must be an organization administrator to perform this action."

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.status != AccountStatus.ACTIVE:
            return False

        # Check if user has any admin/owner membership
        from accounts.models import TenantMembership

        return TenantMembership.objects.filter(
            user=request.user,
            is_active=True,
            role__in=MembershipRole.ADMIN_ROLES,
        ).exists()


class IsOrganizationMember(BasePermission):
    """
    Allow access to any user who is an active member of any organization.

    Used for endpoints where any organization member can access data.
    """

    message = "You must be a member of an organization to access this resource."

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.status != AccountStatus.ACTIVE:
            return False

        from accounts.models import TenantMembership

        return TenantMembership.objects.filter(
            user=request.user,
            is_active=True,
        ).exists()


class CanViewPublicOrganization(BasePermission):
    """
    Public organizations can be viewed by anyone, including unauthenticated users.
    Used for public listing and detail endpoints.
    """

    def has_permission(self, request: Request, view: APIView) -> bool:
        return True
