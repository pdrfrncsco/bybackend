"""
BOLAYETU — Common Permissions
Tenant-aware permission classes used across all apps.
Skill: BOLAYETU_SECURITY_SKILL
"""

from rest_framework.permissions import BasePermission
import logging

logger = logging.getLogger('bolayetu')


class IsTenantMember(BasePermission):
    """
    Allows access only to users who belong to the current request.tenant.
    The user's primary tenant must match request.tenant.
    """
    message = 'You do not belong to this tenant.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        tenant = getattr(request, 'tenant', None)
        if tenant is None:
            return False
        return request.user.tenant == tenant


class IsTenantAdmin(IsTenantMember):
    """
    Allows access only to organisation admins of the current tenant.
    """
    message = 'You are not an admin of this tenant.'

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        tenant = getattr(request, 'tenant', None)
        return request.user.has_role('org_admin', tenant=tenant)


class IsTenantStaff(IsTenantMember):
    """
    Allows access to org admins AND org staff of the current tenant.
    """
    message = 'You are not a staff member of this tenant.'

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        tenant = getattr(request, 'tenant', None)
        return (
            request.user.has_role('org_admin', tenant=tenant)
            or request.user.has_role('org_staff', tenant=tenant)
        )


class IsClubAdmin(BasePermission):
    """Allows access to club admins."""
    message = 'You are not the admin of this club.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        tenant = getattr(request, 'tenant', None)
        return request.user.has_role('club_admin', tenant=tenant)


class IsClubStaff(BasePermission):
    """Allows club admin and club staff."""
    message = 'You are not a staff member of this club.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        tenant = getattr(request, 'tenant', None)
        return (
            request.user.has_role('club_admin', tenant=tenant)
            or request.user.has_role('club_staff', tenant=tenant)
        )


class IsPlayer(BasePermission):
    """Allows only players to access their own data."""
    message = 'You do not have a player profile.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role == 'jogador'


class IsPlatformAdmin(BasePermission):
    """Platform superadmin — cross-tenant access."""
    message = 'Platform admin access required.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.is_superuser or request.user.role == 'superadmin'


class IsTenantMemberOrReadOnly(IsTenantMember):
    """
    Safe reads for anyone; writes only for tenant members.
    Use for public-facing endpoints that also have authenticated actions.
    """
    SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')

    def has_permission(self, request, view):
        if request.method in self.SAFE_METHODS:
            return True
        return super().has_permission(request, view)


class HasTenantPermission(BasePermission):
    """
    Checks a specific permission code against the user's roles.

    Usage in ViewSet:
        permission_classes = [IsAuthenticated, HasTenantPermission]
        required_permission = 'competitions:manage_fixtures'
    """
    message = 'You do not have the required permission.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        required_permission = getattr(view, 'required_permission', None)
        if not required_permission:
            return True

        tenant = getattr(request, 'tenant', None)
        return request.user.has_permission(required_permission, tenant=tenant)
