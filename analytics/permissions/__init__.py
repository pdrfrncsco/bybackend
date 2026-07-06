from rest_framework.permissions import BasePermission
from accounts.selectors import TenantMembershipSelector
from accounts.models import TenantMembership


class CanViewTenantAnalytics(BasePermission):
    """
    Permission class to ensure that users can only view analytics for tenants
    they are active members of (unless they are superusers/staff).
    """

    message = "You do not belong to this organization."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Superusers and staff have access to all
        if request.user.is_superuser or request.user.is_staff:
            return True

        tenant = getattr(request, "tenant", None)
        if not tenant:
            return True  # If no tenant in request context, let the view decide or check logic.

        membership = TenantMembershipSelector.get_membership(
            user=request.user,
            tenant_id=tenant.id,
        )
        return membership is not None and membership.is_active


class CanManageReports(BasePermission):
    """
    Permission to request, generate and view reports.
    Requires active membership in the target tenant.
    """

    message = "You do not have permission to manage reports for this organization."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser or request.user.is_staff:
            return True

        tenant = getattr(request, "tenant", None)
        if not tenant:
            # If it's a global action, require at least one active membership
            return TenantMembership.objects.filter(user=request.user, is_active=True).exists()

        membership = TenantMembershipSelector.get_membership(
            user=request.user,
            tenant_id=tenant.id,
        )
        return membership is not None and membership.is_active
