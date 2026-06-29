"""
BOLAYETU — Clubs Permissions

RBAC permission classes for the clubs domain.

Architecture rule:
    Permissions are NEVER checked inside services.
    They are evaluated by DRF at the view level, before the service is called.
"""

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from accounts.constants import AccountStatus


class CanViewPublicClub(BasePermission):
    """
    Public clubs can be viewed by anyone, including unauthenticated users.
    """

    def has_permission(self, request: Request, view: APIView) -> bool:
        return True


class IsClubAdmin(BasePermission):
    """
    Allow access only to users who are admins of a club.

    This checks if the user is either:
        1. A tenant admin/owner of the club's organization, OR
        2. A MANAGER or PRESIDENT of any club.
    """

    message = "You must be a club administrator to perform this action."

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.status != AccountStatus.ACTIVE:
            return False

        from accounts.constants import MembershipRole
        from accounts.models import TenantMembership
        from clubs.constants import ClubMemberRole
        from clubs.models import ClubMember

        # Check if user is a tenant admin
        is_tenant_admin = TenantMembership.objects.filter(
            user=request.user,
            is_active=True,
            role__in=MembershipRole.ADMIN_ROLES,
        ).exists()

        if is_tenant_admin:
            return True

        # Check if user is a club admin
        return ClubMember.objects.filter(
            user=request.user,
            is_active=True,
            role__in=ClubMemberRole.ADMIN_ROLES,
        ).exists()


class IsClubMember(BasePermission):
    """
    Allow access to any user who is an active member of any club.
    """

    message = "You must be a member of a club to access this resource."

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.status != AccountStatus.ACTIVE:
            return False

        from clubs.models import ClubMember

        return ClubMember.objects.filter(
            user=request.user,
            is_active=True,
        ).exists()
