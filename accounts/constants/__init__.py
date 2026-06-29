"""
BOLAYETU — Accounts Constants

Centralized constants for the accounts domain.
All choices, limits and defaults are defined here.
"""


class ProfileType:
    """
    Defines the type of business profile a user can have.

    A user can only have ONE active profile type at a time.
    The profile type determines the user's role and available features.
    """

    ADMIN = "admin"
    ORGANIZATION = "organization"
    CLUB = "club"
    PLAYER = "player"
    FAN = "fan"

    CHOICES = [
        (ADMIN, "Platform Admin"),
        (ORGANIZATION, "Organization"),
        (CLUB, "Club"),
        (PLAYER, "Player"),
        (FAN, "Fan"),
    ]

    ALL = [ADMIN, ORGANIZATION, CLUB, PLAYER, FAN]


class MembershipRole:
    """
    Defines the role a user can have within a Tenant.

    Roles follow the RBAC model defined in the security architecture.
    """

    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    MEMBER = "member"

    CHOICES = [
        (OWNER, "Owner"),
        (ADMIN, "Admin"),
        (MANAGER, "Manager"),
        (MEMBER, "Member"),
    ]

    ALL = [OWNER, ADMIN, MANAGER, MEMBER]

    # Roles with administrative access
    ADMIN_ROLES = [OWNER, ADMIN]


class AccountStatus:
    """User account status values."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"
    DEACTIVATED = "deactivated"

    CHOICES = [
        (ACTIVE, "Active"),
        (SUSPENDED, "Suspended"),
        (PENDING_VERIFICATION, "Pending Verification"),
        (DEACTIVATED, "Deactivated"),
    ]


class LanguageCode:
    """Supported language codes."""

    PORTUGUESE = "pt"
    ENGLISH = "en"
    FRENCH = "fr"

    CHOICES = [
        (PORTUGUESE, "Português"),
        (ENGLISH, "English"),
        (FRENCH, "Français"),
    ]

    DEFAULT = PORTUGUESE


class TimezoneDefault:
    """Default timezone for Angolan users."""

    LUANDA = "Africa/Luanda"


# Password policy
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128

# Token expiry (in minutes)
EMAIL_VERIFICATION_TOKEN_EXPIRY = 24 * 60  # 24 hours
PASSWORD_RESET_TOKEN_EXPIRY = 60  # 1 hour
