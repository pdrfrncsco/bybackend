"""
BOLAYETU — Transfer Permissions

Custom permissions for transfer operations.
"""

from rest_framework.permissions import BasePermission

from accounts.models import TenantMembership


class CanCreateTransfer(BasePermission):
    """
    Permission to create a transfer request.

    User must be a member of the destination club's tenant.
    """

    message = "You do not have permission to create a transfer for this club."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        to_club_id = request.data.get("to_club_id")
        if not to_club_id:
            return True  # Let validation handle missing club

        # Check if user belongs to the destination club's tenant
        from clubs.models import Club

        try:
            club = Club.objects.get(id=to_club_id)
            return TenantMembership.objects.filter(
                user=request.user,
                tenant=club.tenant,
            ).exists()
        except Club.DoesNotExist:
            return True  # Let validation handle invalid club


class CanApproveRejectTransfer(BasePermission):
    """
    Permission to approve or reject a transfer.

    User must be a member of the ORIGIN club's tenant.
    For free agent transfers (no origin club), any authenticated user can approve.
    """

    message = "Only the origin club can approve or reject this transfer."

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        # If no origin club (free agent), allow any authenticated user
        if not obj.from_club:
            return True

        # Check if user belongs to the origin club's tenant
        return TenantMembership.objects.filter(
            user=request.user,
            tenant=obj.from_tenant,
        ).exists()


class CanViewTransfer(BasePermission):
    """
    Permission to view a transfer.

    User must be a member of either the origin or destination tenant.
    """

    message = "You do not have permission to view this transfer."

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user belongs to origin tenant
        if obj.from_tenant:
            if TenantMembership.objects.filter(
                user=request.user,
                tenant=obj.from_tenant,
            ).exists():
                return True

        # Check if user belongs to destination tenant
        return TenantMembership.objects.filter(
            user=request.user,
            tenant=obj.to_tenant,
        ).exists()


class CanManageTransfers(BasePermission):
    """
    General permission for transfer management.

    User must be a member of a tenant to access transfer operations.
    """

    message = "You must be a member of an organization to manage transfers."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        return TenantMembership.objects.filter(user=request.user).exists()
