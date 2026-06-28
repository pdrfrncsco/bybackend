"""
BOLAYETU — Accounts Permissions

RBAC permission classes for the accounts domain.

Architecture rule:
    Permissions are NEVER checked inside services.
    They are evaluated by DRF at the view level, before the service is called.
    Object-level permissions (ownership) are checked via has_object_permission.
"""

from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.views import APIView

from accounts.constants import AccountStatus


class IsActiveAccount(BasePermission):
    """
    Allow access only to users with an ACTIVE account status.

    This goes beyond DRF's IsAuthenticated, which only checks
    that the user is authenticated. This permission also verifies
    that the account has not been suspended or deactivated.
    """

    message = "Your account is not active. Please contact support."

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.status == AccountStatus.ACTIVE
        )


class IsAccountOwner(BasePermission):
    """
    Object-level permission: only the account owner can access their own data.

    Used for endpoints like /me/, /change-password/, etc.
    """

    message = "You do not have permission to access this account."

    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
        return bool(request.user and request.user.is_authenticated and obj == request.user)


class IsPlatformAdmin(BasePermission):
    """
    Allow access only to Django superusers (platform administrators).

    Platform admins have unrestricted access to all resources.
    """

    message = "You must be a platform administrator to access this resource."

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_superuser
        )
