"""
BOLAYETU — TenantMembership Model

Represents the relationship between a User and a Tenant.

Architecture principle (06A_GLOBAL_AND_TENANT_DOMAIN.md):
    The User is a GLOBAL entity.
    Belonging to a Tenant is a contextual relationship, not an intrinsic property.

    A user can belong to multiple Tenants (e.g. a platform admin managing
    multiple federations). Each membership has its own role.

Examples:
    - Pedro → FAF (role: ADMIN)
    - Pedro → Girabola (role: MEMBER)
    - Maria → APF Luanda (role: OWNER)
"""

from django.conf import settings
from django.db import models

from accounts.constants import MembershipRole
from common.models import BaseModel


class TenantMembership(BaseModel):
    """
    Bridge between User (Global) and Tenant (Tenant-domain).

    Each membership record grants a user access to a specific
    organization with a specific role.

    Uniqueness constraint:
        A user can only have ONE active membership per Tenant.
        Multiple roles within the same tenant are not supported;
        the role is changed by updating the existing membership.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="memberships",
        verbose_name="User",
    )
    tenant = models.ForeignKey(
        "core.Tenant",
        on_delete=models.CASCADE,
        related_name="memberships",
        verbose_name="Tenant",
    )
    role = models.CharField(
        max_length=20,
        choices=MembershipRole.CHOICES,
        default=MembershipRole.MEMBER,
        verbose_name="Role",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Is Active",
    )

    # Who added this user to the tenant
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invitations_sent",
        verbose_name="Invited By",
    )

    joined_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Joined At",
    )

    class Meta:
        ordering = ["-joined_at"]
        verbose_name = "Tenant Membership"
        verbose_name_plural = "Tenant Memberships"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "tenant"],
                name="unique_user_tenant_membership",
            )
        ]

    def __str__(self) -> str:
        return f"{self.user} → {self.tenant} ({self.role})"

    @property
    def is_admin(self) -> bool:
        """Returns True if the member has administrative privileges."""
        return self.role in MembershipRole.ADMIN_ROLES

    def deactivate(self) -> None:
        """Remove the user's active access to this tenant."""
        self.is_active = False
        self.save(update_fields=["is_active"])

    def promote(self, new_role: str) -> None:
        """Change the member's role within the tenant."""
        if new_role not in MembershipRole.ALL:
            raise ValueError(f"Invalid role: {new_role}")
        self.role = new_role
        self.save(update_fields=["role"])
