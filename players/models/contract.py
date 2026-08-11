"""
BOLAYETU — PlayerContract Model

Represents a professional contract between a player and a club.
"""

from django.db import models
from common.models import BaseModel


class PlayerContract(BaseModel):
    """Professional contract between Player and Club."""

    class ContractType(models.TextChoices):
        PROFESSIONAL = "professional", "Profissional"
        YOUTH = "youth", "Juniores"
        AMATEUR = "amateur", "Amador"
        SHORT_TERM = "short_term", "Curto Prazo"
        TRIAL = "trial", "Período de Teste"
        LOAN = "loan", "Empréstimo"
        EXTENSION = "extension", "Renovação"

    class ContractStatus(models.TextChoices):
        DRAFT = "draft", "Rascunho"
        ACTIVE = "active", "Ativo"
        EXPIRED = "expired", "Expirado"
        TERMINATED = "terminated", "Terminado"
        SUSPENDED = "suspended", "Suspenso"

    # Basic Relations
    player = models.ForeignKey(
        "players.Player",
        on_delete=models.CASCADE,
        related_name="contracts",
        verbose_name="Jogador",
    )
    club = models.ForeignKey(
        "clubs.Club",
        on_delete=models.CASCADE,
        related_name="player_contracts",
        verbose_name="Clube",
    )
    tenant = models.ForeignKey(
        "core.Tenant",
        on_delete=models.CASCADE,
        related_name="player_contracts",
        verbose_name="Organização",
    )

    # Contract Terms
    contract_type = models.CharField(
        max_length=20,
        choices=ContractType.choices,
        default=ContractType.PROFESSIONAL,
        verbose_name="Tipo de Contrato",
    )
    status = models.CharField(
        max_length=20,
        choices=ContractStatus.choices,
        default=ContractStatus.DRAFT,
        verbose_name="Estado",
    )

    # Dates
    start_date = models.DateField(verbose_name="Data de Início")
    end_date = models.DateField(verbose_name="Data de Fim")
    signed_date = models.DateTimeField(null=True, blank=True, verbose_name="Data de Assinatura")

    # Financial
    salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Salário",
    )
    currency = models.CharField(
        max_length=3,
        default="USD",
        verbose_name="Moeda",
    )
    bonuses = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Bónus",
        help_text="Estrutura: {'appearance': 500, 'goal': 1000, 'win': 2000}",
    )
    release_clause = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Cláusula de Rescisão",
    )

    # Contract Clauses
    has_image_rights = models.BooleanField(
        default=False,
        verbose_name="Direitos de Imagem",
    )
    option_year = models.BooleanField(
        default=False,
        verbose_name="Opção de Renovação",
    )
    termination_clause = models.TextField(
        blank=True,
        verbose_name="Cláusula de Rescisão",
    )

    # Documentation
    contract_document = models.ForeignKey(
        "media_assets.MediaAsset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="player_contracts",
        verbose_name="Documento do Contrato",
    )

    # Signatures
    signed_by_player = models.BooleanField(
        default=False,
        verbose_name="Assinado por Jogador",
    )
    signed_by_club = models.BooleanField(
        default=False,
        verbose_name="Assinado por Clube",
    )
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data de Verificação",
    )
    verified_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_player_contracts",
        verbose_name="Verificado Por",
    )

    class Meta:
        verbose_name = "Contrato do Jogador"
        verbose_name_plural = "Contratos de Jogadores"
        ordering = ["-start_date"]
        # Ensure only one active contract per player per club
        constraints = [
            models.UniqueConstraint(
                fields=["player", "club", "start_date"],
                name="unique_active_contract_per_player_club",
                condition=models.Q(status__in=["active", "draft"]),
            )
        ]

    def __str__(self) -> str:
        return f"{self.player.full_name} @ {self.club.name} ({self.start_date.year})"

    @property
    def is_active(self) -> bool:
        from datetime import date
        return (
            self.status == self.ContractStatus.ACTIVE
            and self.start_date <= date.today() <= self.end_date
        )

    @property
    def is_fully_signed(self) -> bool:
        return self.signed_by_player and self.signed_by_club
