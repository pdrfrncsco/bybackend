"""
BOLAYETU — Organization Subscription Model

Represents a fan/user subscription to an organization (tenant).

This is different from TenantMembership:
    - TenantMembership: User is a STAFF MEMBER of the organization (admin, manager, etc.)
    - OrganizationSubscription: User is a FOLLOWER/SUBSCRIBER of the organization (fan)

Architecture:
    - Subscriptions are GLOBAL (not tenant-scoped) — a user can follow multiple organizations.
    - Subscriptions do NOT grant any management permissions.
    - Subscriptions enable notifications and personalized content feeds.
"""

from django.conf import settings
from django.db import models

from common.models import BaseModel


class OrganizationSubscription(BaseModel):
    """
    Represents a user's subscription (follow) to an organization.

    This allows fans/adepts to follow organizations and receive
    updates about their competitions, matches, and news.

    A user can subscribe to multiple organizations.
    An organization can have many subscribers.

    Uniqueness:
        A user can only have ONE active subscription per organization.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organization_subscriptions",
        verbose_name="User",
    )
    tenant = models.ForeignKey(
        "core.Tenant",
        on_delete=models.CASCADE,
        related_name="subscriptions",
        verbose_name="Organization",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Is Active",
    )
    subscribed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Subscribed At",
    )

    class Meta:
        ordering = ["-subscribed_at"]
        verbose_name = "Organization Subscription"
        verbose_name_plural = "Organization Subscriptions"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "tenant"],
                name="unique_user_organization_subscription",
            )
        ]

    def __str__(self) -> str:
        return f"{self.user} → {self.tenant}"

    def deactivate(self) -> None:
        """Deactivate the subscription (unsubscribe)."""
        self.is_active = False
        self.save(update_fields=["is_active"])

    def reactivate(self) -> None:
        """Reactivate a previously deactivated subscription."""
        self.is_active = True
        self.save(update_fields=["is_active"])
