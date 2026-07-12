"""
BOLAYETU — Player Permissions

Custom DRF permissions for player endpoints.

Public endpoints (list, detail, search) are open to AllowAny.
Write endpoints (create, update) are restricted to platform staff (is_staff).
Registration endpoints are restricted to authenticated org members.
"""

from rest_framework.permissions import BasePermission, IsAuthenticated


class IsStaffOrReadOnly(BasePermission):
    """
    Allow any user to read (GET).
    Only staff members can write (POST, PUT, PATCH, DELETE).

    Used for the global Player entity since players are not tenant-owned.
    """

    def has_permission(self, request, view) -> bool:
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class CanManagePlayerRegistrations(IsAuthenticated):
    """
    Authenticated users who belong to the tenant that owns the club
    can manage player registrations.

    Fine-grained object-level permission checks are done in the view
    by verifying that request.user has a TenantMembership for the club's tenant.
    """

    message = "You must be a member of this organization to manage player registrations."


class CanManagePlayerProfile(BasePermission):
    """
    Staff can manage any player profile.
    Authenticated users can manage their own linked player profile.
    """

    message = "You do not have permission to manage this player profile."

    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_authenticated)

    @staticmethod
    def can_manage(*, user, player: "Player") -> bool:
        if user.is_staff:
            return True
        from players.selectors import PlayerSelector

        linked = PlayerSelector.get_for_user(user)
        return linked is not None and linked.id == player.id
