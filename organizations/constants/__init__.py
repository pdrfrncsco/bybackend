"""
BOLAYETU — Organizations Constants

Centralized constants for the organizations domain.
Reuses TenantType and TenantStatus from core.models.Tenant.
"""


class OrganizationType:
    """
    Defines the type of organization.
    Mirrors core.Tenant.TenantType for use in serializers and API.
    """

    FEDERATION = "federation"
    ASSOCIATION = "association"
    LEAGUE = "league"
    ORGANIZER = "organizer"
    ACADEMY = "academy"

    CHOICES = [
        (FEDERATION, "Federação"),
        (ASSOCIATION, "Associação"),
        (LEAGUE, "Liga"),
        (ORGANIZER, "Organizador"),
        (ACADEMY, "Academia"),
    ]

    ALL = [FEDERATION, ASSOCIATION, LEAGUE, ORGANIZER, ACADEMY]

    LABELS = {
        FEDERATION: "Federação",
        ASSOCIATION: "Associação",
        LEAGUE: "Liga",
        ORGANIZER: "Organizador",
        ACADEMY: "Academia",
    }


class OrganizationStatus:
    """
    Defines the status of an organization.
    Mirrors core.Tenant.TenantStatus.
    """

    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"

    CHOICES = [
        (PENDING, "Pendente"),
        (ACTIVE, "Ativa"),
        (SUSPENDED, "Suspensa"),
        (CLOSED, "Encerrada"),
    ]

    ALL = [PENDING, ACTIVE, SUSPENDED, CLOSED]


# Maximum file size for logo uploads (5 MB)
MAX_LOGO_SIZE = 5 * 1024 * 1024

# Allowed logo file types
ALLOWED_LOGO_TYPES = ["image/jpeg", "image/png", "image/webp", "image/svg+xml"]
