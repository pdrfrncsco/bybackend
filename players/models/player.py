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
        ACTIVE = "active", "Activo"
        RETIRED = "retired", "Retiredo"
        BANNED = "banned", "Banido"
        INACTIVE = "inactive", "Inactivo"

    class Position(models.TextChoices):
        # GK - Goalkeeper
        GK = "gk", "Guarda-redes"
        
        # Defence
        CB = "cb", "Defesa Central"
        LB = "lb", "Defesa Esquerda"
        RB = "rb", "Defesa Direita"
        LWB = "lwb", "Lateral Esquerda"
        RWB = "rwb", "Lateral Direita"
        
        # Midfield
        CM = "cm", "Meio-Campo"
        CDM = "cdm", "Meio-Campo Defensivo"
        CAM = "cam", "Meio-Campo Ofensivo"
        LM = "lm", "Meio-Campo Esquerda"
        RM = "rm", "Meio-Campo Direito"
        LW = "lw", "Atacante Esquerda"
        RW = "rw", "Atacante Direito"
        
        # Attack
        ST = "st", "Avançado"
        CF = "cf", "Centro-avante"
        MULTIPLE = "multiple", "Varios Posições"

    # Personal Information
    first_name = models.CharField(max_length=255, verbose_name="Primeiro Nome")
    last_name = models.CharField(max_length=255, verbose_name="Apelido")
    slug = models.SlugField(max_length=255, unique=True, blank=True, verbose_name="Slug")
    
    # Contact
    email = models.EmailField(null=True, blank=True, unique=True, verbose_name="Email")
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name="Telefone")
    
    # Physical
    date_of_birth = models.DateField(null=True, blank=True, verbose_name="Data de Nascimento")
    nationality = models.CharField(max_length=100, null=True, blank=True, verbose_name="País")
    height_cm = models.IntegerField(null=True, blank=True, verbose_name="Altura (cm)")
    weight_kg = models.IntegerField(null=True, blank=True, verbose_name="Peso (kg)")
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
    shirt_number = models.IntegerField(null=True, blank=True, verbose_name="Número de Camisa Preferido")
    # Profile
    bio = models.TextField(null=True, blank=True, verbose_name="Biografia")
    avatar = models.URLField(max_length=500, null=True, blank=True, verbose_name="Avatar URL")
    is_public = models.BooleanField(default=True, verbose_name="É Público?")
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=PlayerStatus.choices,
        default=PlayerStatus.ACTIVE,
        verbose_name="Status do Jogador",
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
    total_matches = models.IntegerField(default=0, verbose_name="Total de Jogos Jogados")
    total_goals = models.IntegerField(default=0, verbose_name="Total de Gols Feitos")
    total_assists = models.IntegerField(default=0, verbose_name="Total de Assistências")
    
    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Jogador"
        verbose_name_plural = "Jogadores"
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
        dob = self.date_of_birth
        # Defensive: handle cases where dob is stored / passed as a string
        if isinstance(dob, str):
            try:
                dob = date.fromisoformat(dob)
            except ValueError:
                return None
        today = date.today()
        return today.year - dob.year - (
            (today.month, today.day) < (dob.month, dob.day)
        )
    
    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            base = slugify(self.full_name)
            slug = base
            counter = 1
            while Player.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
