"""
BOLAYETU — Agent and PlayerAgentRelationship Models

Represents sports agents and their representation agreements with players.
"""

from django.db import models
from common.models import BaseModel


class Agent(BaseModel):
    """Sports agent (independent business entity)."""

    class AgencyType(models.TextChoices):
        INDIVIDUAL = "individual", "Individual Freelancer"
        AGENCY = "agency", "Sports Agency"
        FIRM = "firm", "Law Firm"

    name = models.CharField(max_length=255, verbose_name="Nome do Agente")
    agency_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Nome da Agência",
    )
    agency_type = models.CharField(
        max_length=20,
        choices=AgencyType.choices,
        default=AgencyType.INDIVIDUAL,
        verbose_name="Tipo de Agência",
    )

    # Credentials
    license_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Número de Licença",
    )
    fifa_agent_id = models.CharField(
        max_length=100,
        blank=True,
        unique=True,
        verbose_name="ID FIFA Connect",
    )

    # Contact
    country = models.CharField(max_length=3, verbose_name="País")
    email = models.EmailField(verbose_name="Email")
    phone = models.CharField(max_length=20, verbose_name="Telefone")
    website = models.URLField(blank=True, verbose_name="Website")

    # Address
    address = models.TextField(blank=True, verbose_name="Endereço")
    city = models.CharField(max_length=100, blank=True, verbose_name="Cidade")
    postal_code = models.CharField(max_length=20, blank=True, verbose_name="Código Postal")

    # Status
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    verified = models.BooleanField(default=False, verbose_name="Verificado")
    verified_at = models.DateTimeField(null=True, blank=True, verbose_name="Data de Verificação")

    class Meta:
        verbose_name = "Agente"
        verbose_name_plural = "Agentes"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["fifa_agent_id"]),
            models.Index(fields=["country"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.agency_name or 'Independent'})"


class PlayerAgentRelationship(BaseModel):
    """Representation agreement between a player and an agent."""

    class RelationshipStatus(models.TextChoices):
        ACTIVE = "active", "Ativo"
        EXPIRED = "expired", "Expirado"
        TERMINATED = "terminated", "Terminado"
        SUSPENDED = "suspended", "Suspenso"

    # Core Relations
    player = models.ForeignKey(
        "players.Player",
        on_delete=models.CASCADE,
        related_name="agent_relationships",
        verbose_name="Jogador",
    )
    agent = models.ForeignKey(
        Agent,
        on_delete=models.CASCADE,
        related_name="player_relationships",
        verbose_name="Agente",
    )

    # Tenant
    tenant = models.ForeignKey(
        "core.Tenant",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="player_agent_relationships",
        verbose_name="Organização",
    )

    # Dates
    start_date = models.DateField(verbose_name="Data de Início")
    end_date = models.DateField(null=True, blank=True, verbose_name="Data de Término")

    # Status
    status = models.CharField(
        max_length=20,
        choices=RelationshipStatus.choices,
        default=RelationshipStatus.ACTIVE,
        verbose_name="Estado",
    )

    # Financial
    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Taxa de Comissão (%)",
    )

    # Documentation
    representation_agreement = models.ForeignKey(
        "media_assets.MediaAsset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="player_agent_relationships",
        verbose_name="Documento de Acordo",
    )

    # Notes
    notes = models.TextField(blank=True, verbose_name="Notas")

    class Meta:
        verbose_name = "Representação do Jogador"
        verbose_name_plural = "Representações de Jogadores"
        ordering = ["-start_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["player", "agent"],
                name="unique_active_agent_per_player",
                condition=models.Q(status="active"),
            )
        ]

    def __str__(self) -> str:
        return f"{self.player.full_name} <> {self.agent.name}"

    @property
    def is_active(self) -> bool:
        from datetime import date
        today = date.today()
        if self.status != self.RelationshipStatus.ACTIVE:
            return False
        if self.start_date > today:
            return False
        if self.end_date and self.end_date < today:
            return False
        return True
