"""
BOLAYETU — Player Model

Represents a footballer as a GLOBAL entity.

Architecture (06A_GLOBAL_AND_TENANT_DOMAIN.md):
    - Player is GLOBAL — never belongs to a specific tenant/organization
    - A player's career spans multiple clubs, competitions, tenants
    - Tenants only create PlayerRegistration records (temporary bindings)
    - Career history is built automatically via registrations and transfers
    - This is the opposite of current ClubMember(role=player) which is tenant-scoped
"""

from django.db import models
from django.utils.text import slugify

from common.models import BaseModel


class Player(BaseModel):
    """
    Represents a footballer as an independent, reusable global entity.
    
    A Player can:
        - Be registered in multiple clubs across different tenants
        - Have a career history across all registrations
        - Have match statistics aggregated across all competitions
        - Be listed publicly on the Bolayetu platform
        - Be part of transfers, trades, and scouting
    
    A Player cannot:
        - Belong exclusively to one tenant/organization
        - Have their history tied to a single club
    
    Identity is based on personal info + optional User link.
    """

    class PlayerStatus(models.TextChoices):
        ACTIVE = "active", "Active"
        RETIRED = "retired", "Retired"
        BANNED = "banned", "Banned"
        INACTIVE = "inactive", "Inactive"

    class Position(models.TextChoices):
        # GK - Goalkeeper
        GK = "gk", "Goalkeeper"
        
        # Defence
        CB = "cb", "Center Back"
        LB = "lb", "Left Back"
        RB = "rb", "Right Back"
        LWB = "lwb", "Left Wing Back"
        RWB = "rwb", "Right Wing Back"
        
        # Midfield
        CM = "cm", "Central Midfielder"
        CDM = "cdm", "Defensive Midfielder"
        CAM = "cam", "Attacking Midfielder"
        LM = "lm", "Left Midfielder"
        RM = "rm", "Right Midfielder"
        LW = "lw", "Left Winger"
        RW = "rw", "Right Winger"
        
        # Attack
        ST = "st", "Striker"
        CF = "cf", "Center Forward"
        MULTIPLE = "multiple", "Multiple Positions"

    # Personal Information
    first_name = models.CharField(max_length=255, verbose_name="First Name")
    last_name = models.CharField(max_length=255, verbose_name="Last Name")
    slug = models.SlugField(max_length=255, unique=True, blank=True, verbose_name="Slug")
    
    # Contact
    email = models.EmailField(null=True, blank=True, unique=True, verbose_name="Email")
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name="Phone")
    
    # Physical
    date_of_birth = models.DateField(null=True, blank=True, verbose_name="Date of Birth")
    nationality = models.CharField(max_length=100, null=True, blank=True, verbose_name="Nationality")
    height_cm = models.IntegerField(null=True, blank=True, verbose_name="Height (cm)")
    weight_kg = models.IntegerField(null=True, blank=True, verbose_name="Weight (kg)")
    foot = models.CharField(
        max_length=10,
        choices=[("left", "Left"), ("right", "Right"), ("both", "Both")],
        null=True,
        blank=True,
        verbose_name="Preferred Foot",
    )
    
    # Football
    primary_position = models.CharField(
        max_length=20,
        choices=Position.choices,
        default=Position.MULTIPLE,
        verbose_name="Primary Position",
    )
    shirt_number = models.IntegerField(null=True, blank=True, verbose_name="Preferred Shirt Number")
    
    # Profile
    bio = models.TextField(null=True, blank=True, verbose_name="Biography")
    avatar = models.URLField(max_length=500, null=True, blank=True, verbose_name="Avatar URL")
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=PlayerStatus.choices,
        default=PlayerStatus.ACTIVE,
        verbose_name="Status",
    )
    
    # Association with User (optional)
    # A player can be linked to a User account (athlete's own profile)
    # But this is optional — scouts/fans manage player profiles too
    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="player_profile",
        verbose_name="Associated User",
    )
    
    # Career statistics (denormalized for fast queries)
    total_matches = models.IntegerField(default=0, verbose_name="Total Matches Played")
    total_goals = models.IntegerField(default=0, verbose_name="Total Goals")
    total_assists = models.IntegerField(default=0, verbose_name="Total Assists")
    
    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Player"
        verbose_name_plural = "Players"
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["status"]),
            models.Index(fields=["nationality"]),
            models.Index(fields=["primary_position"]),
            models.Index(fields=["user"]),
        ]

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self) -> str:
        """Return player's full name."""
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def age(self) -> int | None:
        """Calculate player's current age."""
        if not self.date_of_birth:
            return None
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.full_name)
        super().save(*args, **kwargs)
