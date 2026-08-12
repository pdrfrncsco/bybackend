"""
BOLAYETU — Player Compliance Record Model

Represents FIFA RSTP compliance records for players.
Critical for regulatory compliance, especially for minor transfers and international moves.

Note: FIFA RSTP 2027 rules must be configurable by regulation, not hardcoded.
"""

from django.db import models
from common.models import BaseModel


class PlayerComplianceRecord(BaseModel):
    """Compliance record for a player according to FIFA RSTP rules."""

    class RuleType(models.TextChoices):
        # Transfer Rules
        MINOR_TRANSFER = "minor_transfer", "Transferência de Menor"
        INTERNATIONAL_TRANSFER = "international_transfer", "Transferência Internacional"
        FIRST_REGISTRATION = "first_registration", "Primeiro Registo"
        
        # Work Permit & Documentation
        WORK_PERMIT = "work_permit", "Autorização de Trabalho"
        VISA = "visa", "Visto"
        PASSPORT_VALIDITY = "passport_validity", "Validade do Passaporte"
        
        # Training & Development
        TRAINING_COMPENSATION = "training_compensation", "Compensação de Formação"
        SOLIDARITY_CONTRIBUTION = "solidarity_contribution", "Contribuição de Solidariedade"
        
        # Contract Rules
        CONTRACT_LENGTH = "contract_length", "Duração do Contrato"
        CONTRACT_STABILITY = "contract_stability", "Estabilidade Contratual"
        
        # Registration Windows
        REGISTRATION_WINDOW = "registration_window", "Janela de Registo"
        
        # Other
        OTHER = "other", "Outro"

    class ComplianceStatus(models.TextChoices):
        COMPLIANT = "compliant", "Conforme"
        NON_COMPLIANT = "non_compliant", "Não Conforme"
        PENDING_REVIEW = "pending_review", "Em Revisão"
        EXEMPTION_GRANTED = "exemption_granted", "Isenção Concedida"
        REQUIRES_APPROVAL = "requires_approval", "Requer Aprovação"

    class Priority(models.TextChoices):
        LOW = "low", "Baixa"
        MEDIUM = "medium", "Média"
        HIGH = "high", "Alta"
        CRITICAL = "critical", "Crítica"

    # Relations
    player = models.ForeignKey(
        "players.Player",
        on_delete=models.CASCADE,
        related_name="compliance_records",
        verbose_name="Jogador",
    )
    transfer = models.ForeignKey(
        "transfers.Transfer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="compliance_records",
        verbose_name="Transferência",
        help_text="Transferência associada, se aplicável",
    )

    # Rule Details
    rule_type = models.CharField(
        max_length=30,
        choices=RuleType.choices,
        verbose_name="Tipo de Regra",
    )
    rule_reference = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Referência da Regra",
        help_text="Ex: RSTP Art. 19, Ann. 4, etc.",
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        verbose_name="Prioridade",
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=ComplianceStatus.choices,
        default=ComplianceStatus.PENDING_REVIEW,
        verbose_name="Estado de Conformidade",
    )

    # Details
    description = models.TextField(
        verbose_name="Descrição",
        help_text="Descrição do requisito de conformidade",
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Notas",
        help_text="Observações adicionais sobre o estado de conformidade",
    )

    # Resolution
    resolution_notes = models.TextField(
        blank=True,
        verbose_name="Notas de Resolução",
        help_text="Como a questão de conformidade foi ou deve ser resolvida",
    )
    exemption_reason = models.TextField(
        blank=True,
        verbose_name="Motivo da Isenção",
        help_text="Se isenção foi concedida, justificação",
    )

    # Dates
    deadline = models.DateField(
        null=True,
        blank=True,
        verbose_name="Prazo",
        help_text="Prazo para resolução",
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data de Revisão",
    )
    reviewed_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_compliance_records",
        verbose_name="Revisado Por",
    )

    # Documents
    supporting_documents = models.ManyToManyField(
        "media_assets.MediaAsset",
        blank=True,
        related_name="compliance_records",
        verbose_name="Documentos de Suporte",
    )

    class Meta:
        verbose_name = "Registo de Conformidade"
        verbose_name_plural = "Registos de Conformidade"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["player", "status"]),
            models.Index(fields=["rule_type"]),
            models.Index(fields=["deadline"]),
        ]

    def __str__(self) -> str:
        return f"{self.player.full_name} - {self.get_rule_type_display()}: {self.get_status_display()}"

    @property
    def is_overdue(self) -> bool:
        """Check if compliance deadline has passed."""
        from datetime import date
        if not self.deadline:
            return False
        return (
            self.deadline < date.today()
            and self.status not in [
                self.ComplianceStatus.COMPLIANT,
                self.ComplianceStatus.EXEMPTION_GRANTED,
            ]
        )

    @property
    def requires_action(self) -> bool:
        """Check if compliance record requires action."""
        return self.status in [
            self.ComplianceStatus.PENDING_REVIEW,
            self.ComplianceStatus.NON_COMPLIANT,
            self.ComplianceStatus.REQUIRES_APPROVAL,
        ]

    def mark_compliant(self, reviewed_by, notes: str = "") -> None:
        """Mark the record as compliant."""
        from django.utils import timezone
        self.status = self.ComplianceStatus.COMPLIANT
        self.reviewed_at = timezone.now()
        self.reviewed_by = reviewed_by
        if notes:
            self.resolution_notes = notes
        self.save()

    def mark_non_compliant(self, reviewed_by, notes: str = "") -> None:
        """Mark the record as non-compliant."""
        from django.utils import timezone
        self.status = self.ComplianceStatus.NON_COMPLIANT
        self.reviewed_at = timezone.now()
        self.reviewed_by = reviewed_by
        if notes:
            self.notes = notes
        self.save()
