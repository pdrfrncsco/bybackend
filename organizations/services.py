"""
BOLAYETU — Organizations Service Layer
Skills: BOLAYETU_ARCHITECTURE, BOLAYETU_BACKEND_SKILL, BOLAYETU_MULTITENANT_SKILL
"""

from common.base import BaseService
from core.models import Tenant


class OrganizationService(BaseService):
    """
    Service layer for mutating Organization (Tenant) states.
    """

    @BaseService.atomic
    def update_organization(self, tenant: Tenant, *, data: dict) -> Tenant:
        """
        Updates an organization's fields with validated data.
        """
        # Exclude read-only or system fields from direct user update if necessary
        updatable_fields = [
            'name',
            'type',
            'primary_color',
            'secondary_color',
            'accent_color',
            'country',
            'location',
            'email',
            'phone',
            'website',
            'description',
            'is_public',
        ]

        # In a real setup, we also validate if request.user is a tenant admin.
        # This is handled at the permission layer (TenantAdminPermission).

        for field in updatable_fields:
            if field in data:
                setattr(tenant, field, data[field])

        # Handle logo upload specifically if passed in data
        if 'logo' in data:
            tenant.logo = data['logo']

        tenant.full_clean()
        tenant.save()
        return tenant

    @BaseService.atomic
    def upload_logo(self, tenant: Tenant, *, logo_file) -> Tenant:
        """
        Uploads a logo for the organization.
        """
        tenant.logo = logo_file
        tenant.save()
        return tenant

    @BaseService.atomic
    def subscribe_user(self, *, tenant: Tenant) -> None:
        """
        Subscribes the current user to the organization.
        """
        self._assert_user()
        self.user.subscriptions.add(tenant)

    @BaseService.atomic
    def unsubscribe_user(self, *, tenant: Tenant) -> None:
        """
        Unsubscribes the current user from the organization.
        """
        self._assert_user()
        self.user.subscriptions.remove(tenant)
