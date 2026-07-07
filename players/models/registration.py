"""
BOLAYETU — PlayerRegistration Model

Links a GLOBAL Player to a Tenant's Club for a specific Competition/Season.

Architecture (06A_GLOBAL_AND_TENANT_DOMAIN.md):
    - Player is global, permanent
    - PlayerRegistration is tenant-scoped, temporary (per season/competition)
    - Multiple registrations form a player's career
    - Replaces the old ClubMember(role=player) model
"""

from django.db import models

from common.models import BaseModel


class PlayerRegistration(BaseModel):
    """
    Represents a player's registration with a club for a specific season/competition.
    
    Examples:
        - João registered with Petro for Girabola 2025
        - João registered with TP Mazembe for CAF Champions League 2025
        - João registered with 1º Agosto for Girabola 2026
    
    This model is TENANT-SCOPED (belongs to the tenant that owns the club).
    """

    class RegistrationStatus(models.TextChoices):
        REGISTERED = "registered", "Registered"
        LOANED = "loaned", "On Loan"
        SUSPENDED = "suspended", "Suspended"
        RETIRED = "retired", "Retired"
        TRANSFERRED = "transferred", "Transferred"

    # Player (global)
    player = models.ForeignKey(
        "players.Player",
        on_delete=models.CASCADE,
        related_name="registrations",
        verbose_name="Player",
    )
    
    # Club context (tenant-scoped)
    club = models.ForeignKey(
        "clubs.Club",
        on_delete=models.CASCADE,
        related_name="player_registrations",
        verbose_name="Club",
    )
    
    # Competition context (optional — player might be registered generally without specific competition)
    competition = models.ForeignKey(
        "competitions.Competition",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="player_registrations",
        verbose_name="Competition",
    )
    
    # Tenant (denormalized for query efficiency)
    tenant = models.ForeignKey(
        "core.Tenant",
        on_delete=models.CASCADE,
        related_name="player_registrations",
        verbose_name="Tenant",
    )
    
    # Registration Details
    shirt_number = models.IntegerField(null=True, blank=True, verbose_name="Shirt Number")
    joined_date = models.DateField(verbose_name="Joined Date")
    left_date = models.DateField(null=True, blank=True, verbose_name="Left Date (if transferred)")
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=RegistrationStatus.choices,
        default=RegistrationStatus.REGISTERED,
        verbose_name="Status",
    )
    
    # Career statistics (per club/season)
    matches_played = models.IntegerField(default=0, verbose_name="Matches Played")
    goals = models.IntegerField(default=0, verbose_name="Goals")
    assists = models.IntegerField(default=0, verbose_name="Assists")
    yellow_cards = models.IntegerField(default=0, verbose_name="Yellow Cards")
    red_cards = models.IntegerField(default=0, verbose_name="Red Cards")
    
    class Meta:
        ordering = ["-joined_date"]
        verbose_name = "Player Registration"
        verbose_name_plural = "Player Registrations"
        constraints = [
            models.UniqueConstraint(
                fields=["player", "club", "competition"],
                condition=models.Q(status__in=["registered", "loaned"]),
                name="unique_active_player_club_competition",
            )
        ]
        indexes = [
            models.Index(fields=["club", "status"]),
            models.Index(fields=["player", "status"]),
            models.Index(fields=["tenant", "club"]),
            models.Index(fields=["joined_date"]),
        ]

    def __str__(self) -> str:
        return f"{self.player.full_name} @ {self.club.name} ({self.joined_date.year})"
    
    @property
    def is_active(self) -> bool:
        """Returns True if player is currently registered at this club."""
        return self.status in [self.RegistrationStatus.REGISTERED, self.RegistrationStatus.LOANED]
    
    def deactivate(self, left_date=None) -> None:
        """Mark player as transferred/left from this club."""
        from datetime import date
        self.status = self.RegistrationStatus.TRANSFERRED
        self.left_date = left_date or date.today()
        self.save(update_fields=["status", "left_date"])
