"""
BOLAYETU — Clubs Constants

Centralized constants for the clubs domain.
"""


class ClubStatus:
    """Defines the status of a club."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"

    CHOICES = [
        (ACTIVE, "Ativo"),
        (SUSPENDED, "Suspenso"),
        (INACTIVE, "Inativo"),
    ]

    ALL = [ACTIVE, SUSPENDED, INACTIVE]

    LABELS = {
        ACTIVE: "Ativo",
        SUSPENDED: "Suspenso",
        INACTIVE: "Inativo",
    }


class ClubMemberRole:
    """Defines the role a user can have within a club."""

    PLAYER = "player"
    COACH = "coach"
    ASSISTANT_COACH = "assistant_coach"
    MANAGER = "manager"
    PHYSIO = "physio"
    STAFF = "staff"
    PRESIDENT = "president"

    CHOICES = [
        (PLAYER, "Jogador"),
        (COACH, "Treinador"),
        (ASSISTANT_COACH, "Treinador Adjunto"),
        (MANAGER, "Gestor"),
        (PHYSIO, "Fisioterapeuta"),
        (STAFF, "Staff"),
        (PRESIDENT, "Presidente"),
    ]

    ALL = [PLAYER, COACH, ASSISTANT_COACH, MANAGER, PHYSIO, STAFF, PRESIDENT]

    LABELS = {
        PLAYER: "Jogador",
        COACH: "Treinador",
        ASSISTANT_COACH: "Treinador Adjunto",
        MANAGER: "Gestor",
        PHYSIO: "Fisioterapeuta",
        STAFF: "Staff",
        PRESIDENT: "Presidente",
    }

    # Roles that count as staff (non-players)
    STAFF_ROLES = [COACH, ASSISTANT_COACH, MANAGER, PHYSIO, STAFF, PRESIDENT]

    # Roles with administrative access to club management
    ADMIN_ROLES = [MANAGER, PRESIDENT]


class PlayerPosition:
    """Defines player positions."""

    GOALKEEPER = "GK"
    DEFENDER = "DF"
    MIDFIELDER = "MF"
    FORWARD = "FW"

    CHOICES = [
        (GOALKEEPER, "Guarda-Redes"),
        (DEFENDER, "Defesa"),
        (MIDFIELDER, "Médio"),
        (FORWARD, "Avançado"),
    ]

    ALL = [GOALKEEPER, DEFENDER, MIDFIELDER, FORWARD]

    LABELS = {
        GOALKEEPER: "Guarda-Redes",
        DEFENDER: "Defesa",
        MIDFIELDER: "Médio",
        FORWARD: "Avaçado",
    }


# Maximum file size for logo uploads (5 MB)
MAX_LOGO_SIZE = 5 * 1024 * 1024

# Allowed logo file types
ALLOWED_LOGO_TYPES = ["image/jpeg", "image/png", "image/webp", "image/svg+xml"]

# Jersey number range
MIN_JERSEY_NUMBER = 1
MAX_JERSEY_NUMBER = 99

# Founded year range
MIN_FOUNDED_YEAR = 1800
MAX_FOUNDED_YEAR = 2100
