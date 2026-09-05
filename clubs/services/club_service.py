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
from clubs.constants import ClubMemberRole, ClubStatus
from clubs.exceptions import (
    ClubMemberNotFound,
    ClubNotFound,
    ClubSuspended,
    DuplicateClubMember,
    DuplicateClubName,
    DuplicateJerseyNumber,
    InvalidLogoFile,
    NoClubMembership,
    NotClubAdmin,
)
from clubs.models import Club, ClubMember
from clubs.selectors import ClubSelector
from clubs.validators import validate_logo_file
from core.events import EventType
from core.models import Tenant
from media_assets.constants import AssetVisibility

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
            "name",
            "short_name",
            "primary_color",
            "secondary_color",
            "founded_year",
            "stadium_name",
            "stadium_capacity",
            "city",
            "country",
            "email",
            "phone",
            "website",
            "description",
            "is_public",
        ]

        updated_fields = ["updated_at"]
        for field in updatable_fields:
            if field in kwargs and kwargs[field] is not None:
                setattr(club, field, kwargs[field])
                updated_fields.append(field)

        club.save(update_fields=updated_fields)

        logger.info("Club updated: %s", club.name)
        return club

    @staticmethod
    @transaction.atomic
    def upload_logo(*, club: Club, logo_file=None, file=None, uploaded_by: User = None) -> Club:
        """
        Upload a logo for a club via DAM (Digital Asset Management).

        Creates a MediaAsset (owner_type="club", role="logo") and attaches
        it to the club via MediaUsage.

        See: 08A_DIGITAL_ASSET_MANAGEMENT.md
        """
        logo_file = logo_file or file
        if logo_file is None:
            raise InvalidLogoFile(detail="No logo file provided.")

        validate_logo_file(logo_file)

        from media_assets.exceptions import (
            InvalidMediaFile,
            MediaAssetTooLarge,
            UnsupportedMediaType,
        )
        from media_assets.services import MediaAssetService

        try:
            asset = MediaAssetService.upload_for_owner(
                file=logo_file,
                owner_type="club",
                owner_id=str(club.id),
                name=getattr(logo_file, "name", "Club logo"),
                tenant=club.tenant,
                uploaded_by=uploaded_by,
                role="logo",
                visibility=AssetVisibility.PUBLIC,
            )
        except (InvalidMediaFile, MediaAssetTooLarge, UnsupportedMediaType) as exc:
            raise InvalidLogoFile(detail=str(exc.detail)) from exc

        logger.info("Logo uploaded via DAM for club: %s (asset=%s)", club.name, asset.id)
        return club

    @staticmethod
    @transaction.atomic
    def activate(*, club: Club) -> Club:
        """Activate a club."""
        club.status = ClubStatus.ACTIVE
        club.save(update_fields=["status", "updated_at"])

        ClubService._publish_club_event(club=club, event_type=EventType.CLUB_APPROVED)

        logger.info("Club activated: %s", club.name)
        return club

    @staticmethod
    @transaction.atomic
    def suspend(*, club: Club) -> Club:
        """Suspend a club."""
        club.status = ClubStatus.SUSPENDED
        club.save(update_fields=["status", "updated_at"])

        ClubService._publish_club_event(club=club, event_type=EventType.CLUB_SUSPENDED)

        logger.info("Club suspended: %s", club.name)
        return club

    @staticmethod
    def _publish_club_event(*, club: Club, event_type: str) -> None:
        """Publish a club lifecycle domain event (dispatched after commit)."""
        from core.events import Event, publish_event

        try:
            evt = Event(
                type=event_type,
                payload={"club_id": str(club.id), "club_name": club.name},
                origin="clubs.service",
                tenant_id=str(club.tenant_id) if club.tenant_id else None,
            )
            publish_event(evt)
        except Exception:
            logger.exception("Failed to publish %s event for club %s", event_type, club.id)

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
            existing = ClubMember.objects.filter(club=club, user=user, is_active=True).first()
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

        # Garantir vínculo automático no Tenant (TenantMembership) se o membro for um User
        if user is not None:
            from accounts.models import TenantMembership
            TenantMembership.objects.get_or_create(
                user=user,
                tenant=club.tenant,
                defaults={"role": "member", "is_active": True},
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
            "full_name",
            "role",
            "jersey_number",
            "position",
            "is_active",
            "joined_at",
            "left_at",
        ]

        # Check jersey number conflict if being updated
        if "jersey_number" in kwargs and kwargs["jersey_number"] is not None:
            conflict = (
                ClubMember.objects.filter(
                    club=member.club,
                    jersey_number=kwargs["jersey_number"],
                    is_active=True,
                )
                .exclude(pk=member.pk)
                .exists()
            )
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
        """
        Soft-delete a member by deactivating their membership.
        """
        member.deactivate()
        logger.info("Member removed from club %s: %s", member.club.name, member.display_name)

    @staticmethod
    def get_club_for_user(*, user: User) -> Club:
        """
        Retrieve the club that a user belongs to.

        DEPRECATED: Use get_club_and_verify_admin for administrative operations.

        Args:
            user: The user to look up.

        Returns:
            Club instance that the user belongs to.

        Raises:
            NoClubMembership: If the user is not an active member of any club.
        """
        # Try to find an active club membership for the user
        membership = ClubMember.objects.filter(
            user=user,
            is_active=True
        ).select_related("club", "club__affiliation_request", "club__tenant").first()

        if not membership:
            raise NoClubMembership()

        return membership.club

    @staticmethod
    def get_club_and_verify_admin(*, user: User, club_id: str) -> Club:
        """
        Retrieve a club by ID and verify that the user has administrative rights to it.

        Args:
            user: The user to verify.
            club_id: The UUID of the club.

        Returns:
            The Club instance.

        Raises:
            ClubNotFound: If no club exists with the given ID.
            NotClubAdmin: If the user is not a club admin or tenant admin.
        """
        try:
            club = Club.objects.get(pk=club_id)
        except Club.DoesNotExist:
            raise ClubNotFound()

        from accounts.constants import MembershipRole
        from accounts.models import TenantMembership

        # 1. Check if user is a club admin
        is_club_admin = ClubMember.objects.filter(
            user=user,
            club=club,
            is_active=True,
            role__in=["president", "manager", "coach"],
        ).exists()

        if is_club_admin:
            return club

        # 2. Check if user is a tenant admin for this club's tenant
        is_tenant_admin = TenantMembership.objects.filter(
            user=user,
            tenant=club.tenant,
            is_active=True,
            role__in=MembershipRole.ADMIN_ROLES,
        ).exists()

        if is_tenant_admin:
            return club

        raise NotClubAdmin()

    @staticmethod
    def assert_is_club_admin(*, user: User, club: Club) -> None:
        """
        Verify that a user is a club administrator for the given club.

        Args:
            user: The user to verify.
            club: The club to check.

        Raises:
            NotClubAdmin: If the user is not a club administrator.
        """
        # Check if user has an active membership with admin role
        is_admin = ClubMember.objects.filter(
            user=user,
            club=club,
            is_active=True,
            role__in=["president", "manager", "coach"]  # Admin roles
        ).exists()

        if not is_admin:
            raise NotClubAdmin()
