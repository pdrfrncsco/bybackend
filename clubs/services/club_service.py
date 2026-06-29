"""
BOLAYETU — Club Service

Handles all club-related business logic.

RULES:
    - All business logic lives here, NOT in views.
    - Views only call these methods and return the result.
    - Services raise domain exceptions on failure.
    - All mutations are wrapped in atomic transactions.
"""

import logging

from django.db import transaction

from accounts.models import User
from core.models import Tenant
from clubs.constants import ClubStatus, ClubMemberRole
from clubs.exceptions import (
    ClubNotFound,
    DuplicateClubName,
    ClubSuspended,
    NotClubAdmin,
    NoClubMembership,
    InvalidLogoFile,
    ClubMemberNotFound,
    DuplicateJerseyNumber,
    DuplicateClubMember,
)
from clubs.models import Club, ClubMember
from clubs.selectors import ClubSelector
from clubs.validators import validate_logo_file

logger = logging.getLogger(__name__)


class ClubService:
    """
    Handles club management workflows:
        - Create / update / activate / suspend clubs
        - Logo upload
        - Member management (add, update, remove)
    """

    @staticmethod
    @transaction.atomic
    def create_club(
        *,
        tenant: Tenant,
        name: str,
        **kwargs,
    ) -> Club:
        """
        Create a new club within a tenant.

        Args:
            tenant: The organization the club belongs to.
            name: Club name (must be unique within the tenant).
            **kwargs: Additional club fields (short_name, founded_year,
                stadium_name, city, country, etc.).

        Returns:
            Created Club instance.

        Raises:
            DuplicateClubName: If a club with this name already exists in the tenant.
        """
        if Club.objects.filter(tenant=tenant, name__iexact=name).exists():
            raise DuplicateClubName()

        club = Club.objects.create(
            tenant=tenant,
            name=name,
            **kwargs,
        )

        logger.info("Club created: %s (%s)", club.name, club.id)
        return club

    @staticmethod
    @transaction.atomic
    def update_club(
        *,
        club: Club,
        **kwargs,
    ) -> Club:
        """
        Update a club's information.

        Only non-None values are updated.
        """
        updatable_fields = [
            "name", "short_name", "primary_color", "secondary_color",
            "founded_year", "stadium_name", "stadium_capacity",
            "country", "city", "email", "phone", "website",
            "description", "is_public",
        ]

        updated_fields = ["updated_at"]

        for field in updatable_fields:
            if field in kwargs and kwargs[field] is not None:
                setattr(club, field, kwargs[field])
                updated_fields.append(field)

        club.save(update_fields=updated_fields)

        logger.info("Club updated: %s (%s)", club.name, club.id)
        return club

    @staticmethod
    @transaction.atomic
    def upload_logo(*, club: Club, file) -> Club:
        """
        Upload a logo for a club.
        """
        from django.core.exceptions import ValidationError as DjangoValidationError

        try:
            validate_logo_file(file)
        except DjangoValidationError as exc:
            raise InvalidLogoFile(detail=str(exc.messages[0]) if exc.messages else None)

        from django.core.files.storage import default_storage
        import os

        ext = os.path.splitext(file.name)[1]
        filename = f"club-logos/{club.slug}{ext}"

        saved_path = default_storage.save(filename, file)
        logo_url = default_storage.url(saved_path)

        club.logo = logo_url
        club.save(update_fields=["logo", "updated_at"])

        logger.info("Logo uploaded for club: %s", club.name)
        return club

    @staticmethod
    @transaction.atomic
    def activate(*, club: Club) -> Club:
        """Activate a club."""
        club.status = ClubStatus.ACTIVE
        club.save(update_fields=["status", "updated_at"])

        logger.info("Club activated: %s", club.name)
        return club

    @staticmethod
    @transaction.atomic
    def suspend(*, club: Club) -> Club:
        """Suspend a club."""
        club.status = ClubStatus.SUSPENDED
        club.save(update_fields=["status", "updated_at"])

        logger.info("Club suspended: %s", club.name)
        return club

    @staticmethod
    @transaction.atomic
    def add_member(
        *,
        club: Club,
        user: User | None = None,
        full_name: str | None = None,
        role: str = ClubMemberRole.PLAYER,
        jersey_number: int | None = None,
        position: str | None = None,
        joined_at=None,
    ) -> ClubMember:
        """
        Add a member to a club.

        Raises:
            DuplicateClubMember: If the user is already an active member.
            DuplicateJerseyNumber: If the jersey number is already in use.
        """
        # Check for existing membership
        if user is not None:
            existing = ClubMember.objects.filter(
                club=club, user=user, is_active=True
            ).first()
            if existing:
                raise DuplicateClubMember()

        # Check for jersey number conflict
        if jersey_number is not None:
            conflict = ClubMember.objects.filter(
                club=club,
                jersey_number=jersey_number,
                is_active=True,
            ).exists()
            if conflict:
                raise DuplicateJerseyNumber()

        member = ClubMember.objects.create(
            club=club,
            user=user,
            full_name=full_name,
            role=role,
            jersey_number=jersey_number,
            position=position,
            joined_at=joined_at,
        )

        logger.info("Member added to club %s: %s (%s)", club.name, member.display_name, role)
        return member

    @staticmethod
    @transaction.atomic
    def update_member(
        *,
        member: ClubMember,
        **kwargs,
    ) -> ClubMember:
        """Update a club member's information."""
        updatable_fields = [
            "full_name", "role", "jersey_number", "position",
            "is_active", "joined_at", "left_at",
        ]

        # Check jersey number conflict if being updated
        if "jersey_number" in kwargs and kwargs["jersey_number"] is not None:
            conflict = ClubMember.objects.filter(
                club=member.club,
                jersey_number=kwargs["jersey_number"],
                is_active=True,
            ).exclude(pk=member.pk).exists()
            if conflict:
                raise DuplicateJerseyNumber()

        updated_fields = ["updated_at"]
        for field in updatable_fields:
            if field in kwargs and kwargs[field] is not None:
                setattr(member, field, kwargs[field])
                updated_fields.append(field)

        member.save(update_fields=updated_fields)

        logger.info("Member updated: %s", member.display_name)
        return member

    @staticmethod
    @transaction.atomic
    def remove_member(*, member: ClubMember) -> None:
        """Deactivate a club membership (soft delete)."""
        member.deactivate()
        logger.info("Member removed from club %s: %s", member.club.name, member.display_name)

    @staticmethod
    def assert_is_club_admin(*, user: User, club: Club) -> None:
        """
        Verify that the user has admin privileges for the club.

        Raises:
            NotClubAdmin: If the user is not an admin of this club.
        """
        if not ClubSelector.is_club_admin(user=user, club=club):
            raise NotClubAdmin()

    @staticmethod
    def get_club_for_user(*, user: User) -> Club:
        """
        Get the primary club that the user manages.

        Raises:
            NoClubMembership: If the user has no club membership.
        """
        # Try club admin roles first
        member = (
            ClubMember.objects
            .filter(
                user=user,
                is_active=True,
                role__in=ClubMemberRole.ADMIN_ROLES,
            )
            .select_related("club", "club__tenant")
            .first()
        )

        if member:
            return member.club

        # Fallback: check if user is tenant admin and get first club
        from accounts.constants import MembershipRole
        from accounts.models import TenantMembership

        tenant_admin = (
            TenantMembership.objects
            .filter(
                user=user,
                is_active=True,
                role__in=MembershipRole.ADMIN_ROLES,
            )
            .select_related("tenant")
            .first()
        )

        if tenant_admin:
            club = (
                Club.objects
                .filter(tenant=tenant_admin.tenant, status=ClubStatus.ACTIVE)
                .first()
            )
            if club:
                return club

        raise NoClubMembership()
