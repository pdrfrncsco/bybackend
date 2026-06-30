"""
BOLAYETU — Organization Service

Handles all organization-related business logic.

RULES:
    - All business logic lives here, NOT in views.
    - Views only call these methods and return the result.
    - Services raise domain exceptions on failure.
    - All mutations are wrapped in atomic transactions.
"""

import logging
import os

from django.db import transaction
from django.utils.text import slugify

from accounts.constants import MembershipRole
from accounts.models import User, TenantMembership
from core.models import Tenant
from organizations.exceptions import (
    OrganizationNotFound,
    OrganizationAlreadyExists,
    OrganizationSuspended,
    NotOrganizationAdmin,
    NoOrganizationMembership,
    SubscriptionAlreadyExists,
    SubscriptionNotFound,
    InvalidLogoFile,
)
from organizations.models import OrganizationSubscription
from organizations.selectors import OrganizationSelector
from organizations.validators import validate_logo_file

logger = logging.getLogger(__name__)


class OrganizationService:
    """
    Handles organization management workflows:
        - Profile updates (name, description, branding, contact)
        - Logo upload
        - Fan subscribe / unsubscribe
    """

    @staticmethod
    @transaction.atomic
    def update_organization(
        *,
        tenant: Tenant,
        **kwargs,
    ) -> Tenant:
        """
        Update an organization's profile information.

        Only non-None values are updated. This allows partial updates
        without accidentally overwriting existing data.

        Args:
            tenant: The Tenant instance to update.
            **kwargs: Fields to update (name, type, primary_color,
                secondary_color, country, city, email, phone, website,
                description, is_public, language, timezone).

        Returns:
            Updated Tenant instance.
        """
        updatable_fields = [
            "name", "type", "primary_color", "secondary_color",
            "country", "city", "email", "phone", "website",
            "description", "is_public", "language", "timezone",
        ]

        updated_fields = ["updated_at"]

        for field in updatable_fields:
            if field in kwargs and kwargs[field] is not None:
                setattr(tenant, field, kwargs[field])
                updated_fields.append(field)

        if "name" in kwargs and kwargs["name"] is not None:
            tenant.slug = slugify(kwargs["name"]) or tenant.slug
            if "slug" not in updated_fields:
                updated_fields.append("slug")

        tenant.save(update_fields=list(dict.fromkeys(updated_fields)))

        logger.info("Organization updated: %s (%s)", tenant.name, tenant.id)
        return tenant

    @staticmethod
    @transaction.atomic
    def upload_logo(*, tenant: Tenant, file) -> Tenant:
        """
        Upload a logo for an organization.

        In production, this would upload to Cloudflare R2 and store the URL.
        In development, we store the file URL from Django's media system
        or accept a URL directly.

        Args:
            tenant: The Tenant instance to update.
            file: The uploaded file object.

        Returns:
            Updated Tenant instance with logo URL.

        Raises:
            InvalidLogoFile: If the file is too large or has an invalid type.
        """
        from django.core.exceptions import ValidationError as DjangoValidationError

        try:
            validate_logo_file(file)
        except DjangoValidationError as exc:
            raise InvalidLogoFile(detail=str(exc.messages[0]) if exc.messages else None)

        # In development: save to MEDIA_ROOT and store the URL
        # In production: upload to Cloudflare R2 and store the CDN URL
        # For now, we use Django's default storage
        from django.core.files.storage import default_storage

        ext = os.path.splitext(file.name)[1]
        filename = f"logos/{tenant.id}{ext}"

        # Save the file
        saved_path = default_storage.save(filename, file)
        logo_url = default_storage.url(saved_path)

        tenant.logo = logo_url
        tenant.save(update_fields=["logo", "updated_at"])

        logger.info("Logo uploaded for organization: %s", tenant.name)
        return tenant

    @staticmethod
    @transaction.atomic
    def subscribe(*, user: User, tenant: Tenant) -> OrganizationSubscription:
        """
        Subscribe a user to an organization.

        If an inactive subscription exists, it is reactivated.
        If an active subscription exists, SubscriptionAlreadyExists is raised.

        Args:
            user: The User instance.
            tenant: The Tenant instance.

        Returns:
            OrganizationSubscription instance.

        Raises:
            SubscriptionAlreadyExists: If the user is already actively subscribed.
            OrganizationSuspended: If the organization is suspended.
        """
        if tenant.status in (
            Tenant.TenantStatus.SUSPENDED,
            Tenant.TenantStatus.CLOSED,
        ):
            raise OrganizationSuspended()

        existing = OrganizationSelector.get_subscription(user=user, tenant=tenant)

        if existing:
            if existing.is_active:
                raise SubscriptionAlreadyExists()
            # Reactivate the existing subscription
            existing.reactivate()
            logger.info("Subscription reactivated: %s → %s", user.email, tenant.name)
            return existing

        subscription = OrganizationSubscription.objects.create(
            user=user,
            tenant=tenant,
            is_active=True,
        )

        logger.info("New subscription: %s → %s", user.email, tenant.name)
        return subscription

    @staticmethod
    @transaction.atomic
    def unsubscribe(*, user: User, tenant: Tenant) -> None:
        """
        Unsubscribe a user from an organization.

        Deactivates the subscription (does not delete — history is preserved).

        Args:
            user: The User instance.
            tenant: The Tenant instance.

        Raises:
            SubscriptionNotFound: If the user has no subscription to this organization.
        """
        subscription = OrganizationSelector.get_subscription(user=user, tenant=tenant)

        if subscription is None:
            raise SubscriptionNotFound()

        if not subscription.is_active:
            raise SubscriptionNotFound()

        subscription.deactivate()
        logger.info("Unsubscribed: %s → %s", user.email, tenant.name)

    @staticmethod
    def assert_is_organization_admin(*, user: User, tenant: Tenant) -> None:
        """
        Verify that the user has admin/owner privileges for the organization.

        Args:
            user: The User instance.
            tenant: The Tenant instance.

        Raises:
            NotOrganizationAdmin: If the user is not an admin of this organization.
        """
        from accounts.selectors import TenantMembershipSelector

        membership = TenantMembershipSelector.get_membership(
            user=user,
            tenant_id=tenant.id,
        )

        if membership is None or not membership.is_active:
            raise NotOrganizationAdmin()

        if membership.role not in MembershipRole.ADMIN_ROLES:
            raise NotOrganizationAdmin()

    @staticmethod
    def get_organization_for_user(*, user: User) -> Tenant:
        """
        Get the organization that the authenticated user manages.

        Args:
            user: The authenticated User instance.

        Returns:
            Tenant instance.

        Raises:
            NoOrganizationMembership: If the user has no organization membership.
        """
        tenant = OrganizationSelector.get_for_user(user=user)

        if tenant is None:
            raise NoOrganizationMembership()

        return tenant

    @staticmethod
    def create_organization_with_owner(
        *,
        user: User,
        name: str,
        org_type: str,
        country: str = "Angola",
        city: str | None = None,
    ) -> Tenant:
        """
        Create a pending organization and assign the user as owner.

        Used during organization owner registration / onboarding bootstrap.
        """
        if Tenant.objects.filter(name__iexact=name).exists():
            raise OrganizationAlreadyExists()

        tenant = Tenant.objects.create(
            name=name,
            type=org_type,
            country=country,
            city=city,
            status=Tenant.TenantStatus.PENDING,
            is_public=False,
        )

        TenantMembership.objects.create(
            user=user,
            tenant=tenant,
            role=MembershipRole.OWNER,
            is_active=True,
        )

        logger.info(
            "Organization created with owner: %s (%s) → %s",
            tenant.name,
            tenant.id,
            user.email,
        )
        return tenant

    @staticmethod
    @transaction.atomic
    def launch_portal(*, tenant: Tenant) -> dict:
        """
        Activate the organization portal after onboarding.

        Sets the tenant to active/public and promotes draft competitions.
        """
        from competitions.constants import CompetitionStatus
        from competitions.models import Competition

        tenant.status = Tenant.TenantStatus.ACTIVE
        tenant.is_public = True
        tenant.save(update_fields=["status", "is_public", "updated_at"])

        competitions_activated = Competition.objects.filter(
            tenant=tenant,
            status=CompetitionStatus.DRAFT,
        ).update(status=CompetitionStatus.ACTIVE)

        logger.info(
            "Portal launched for organization: %s (%s), competitions activated: %s",
            tenant.name,
            tenant.id,
            competitions_activated,
        )

        portal_url = f"/organizations/{tenant.slug}" if tenant.slug else None

        return {
            "tenant": tenant,
            "competitions_activated": competitions_activated,
            "portal_url": portal_url,
        }
