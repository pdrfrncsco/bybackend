"""
BOLAYETU — ClubMember Model

Represents a member of a football club (player, coach, staff, etc.).

A ClubMember links a User to a Club with a specific role.
This is different from TenantMembership:
    - TenantMembership: User is a STAFF MEMBER of the organization.
    - ClubMember: User is a PLAYER/COACH/STAFF of a specific club.

Architecture:
    - ClubMember is TENANT-SCOPED through the Club's tenant.
    - A user can be a member of multiple clubs (e.g. transferred mid-season).
    - Only one active membership per club per user is allowed.
"""

from django.conf import settings
from django.db import models

from common.models import BaseModel


class ClubMember(BaseModel):
    """
    Represents a member (player, coach, staff) of a football club.

    Fields:
        - user: The platform User (optional — some historical members
          may not have platform accounts).
        - club: The Club this member belongs to.
        - role: Their role within the club.
        - jersey_number: For players (1-99).
        - position: For players (GK, DF, MF, FW).
        - is_active: Whether this membership is currently active.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="club_memberships",
        null=True,
        blank=True,
        verbose_name="User",
    )
    club = models.ForeignKey(
        "clubs.Club",
        on_delete=models.CASCADE,
        related_name="members",
        verbose_name="Club",
    )

    # Member details (for non-user members or overrides)
    full_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Full Name",
        help_text="Used when the member has no platform account.",
    )

    role = models.CharField(
        max_length=20,
        choices=[
            ("player", "Jogador"),
            ("coach", "Treinador"),
            ("assistant_coach", "Treinador Adjunto"),
            ("manager", "Gestor"),
            ("physio", "Fisioterapeuta"),
            ("staff", "Staff"),
            ("president", "Presidente"),
        ],
        default="player",
        verbose_name="Role",
    )

    # Player-specific fields
    jersey_number = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Jersey Number",
    )
    position = models.CharField(
        max_length=10,
        choices=[
            ("GK", "Guarda-Redes"),
            ("DF", "Defesa"),
            ("MF", "Médio"),
            ("FW", "Avançado"),
        ],
        null=True,
        blank=True,
        verbose_name="Position",
    )

    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    joined_at = models.DateField(
        null=True,
        blank=True,
        verbose_name="Joined At",
    )
    left_at = models.DateField(
        null=True,
        blank=True,
        verbose_name="Left At",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Club Member"
        verbose_name_plural = "Club Members"
        constraints = [
            models.UniqueConstraint(
                fields=["club", "user"],
                name="unique_club_member_per_user",
                condition=models.Q(user__isnull=False),
            ),
            models.UniqueConstraint(
                fields=["club", "jersey_number"],
                name="unique_jersey_number_per_club",
                condition=models.Q(jersey_number__isnull=False, is_active=True),
            ),
        ]

    def __str__(self) -> str:
        name = self.full_name or (str(self.user) if self.user else "Unknown")
        return f"{name} ({self.role}) — {self.club.name}"

    @property
    def display_name(self) -> str:
        """Returns the best available name for display."""
        if self.full_name:
            return self.full_name
        if self.user:
            return self.user.full_name
        return "Unknown"

    @property
    def is_player(self) -> bool:
        """Returns True if this member is a player."""
        return self.role == "player"

    @property
    def is_staff(self) -> bool:
        """Returns True if this member is staff (non-player)."""
        return self.role != "player"

    @property
    def role_label(self) -> str:
        """Returns the human-readable role label."""
        labels = dict(self._meta.get_field("role").choices)
        return labels.get(self.role, self.role)

    @property
    def position_label(self) -> str:
        """Returns the human-readable position label."""
        if not self.position:
            return ""
        labels = dict(self._meta.get_field("position").choices)
        return labels.get(self.position, self.position)

    def deactivate(self) -> None:
        """Deactivate this membership."""
        self.is_active = False
        self.save(update_fields=["is_active"])
