"""
BOLAYETU — Player Medical Profile and Medical Document Models

Represents medical data for players with restricted access.
Critical for player health management and FIFA compliance.

Privacy Note: Access restricted to Player, Club Medical Staff, and Authorized Organization only.
"""

from django.db import models
from common.models import BaseModel


class PlayerMedicalProfile(BaseModel):
    """Medical profile for a player with restricted access."""

    class MedicalStatus(models.TextChoices):
        FIT = "fit", "Apto"
        INJURED = "injured", "Lesionado"
        RECOVERING = "recovering", "Em Recuperação"
        SUSPENDED_MEDICAL = "suspended_medical", "Suspenso (Médico)"

    class BloodType(models.TextChoices):
        A_POSITIVE = "A+", "A+"
        A_NEGATIVE = "A-", "A-"
        B_POSITIVE = "B+", "B+"
        B_NEGATIVE = "B-", "B-"
        AB_POSITIVE = "AB+", "AB+"
        AB_NEGATIVE = "AB-", "AB-"
        O_POSITIVE = "O+", "O+"
        O_NEGATIVE = "O-", "O-"
        UNKNOWN = "unknown", "Desconhecido"

    # Relations
    player = models.OneToOneField(
        "players.Player",
        on_delete=models.CASCADE,
        related_name="medical_profile",
        verbose_name="Jogador",
    )

    # Medical Information
    blood_type = models.CharField(
        max_length=10,
        choices=BloodType.choices,
        default=BloodType.UNKNOWN,
        verbose_name="Tipo Sanguíneo",
    )
    medical_status = models.CharField(
        max_length=20,
        choices=MedicalStatus.choices,
        default=MedicalStatus.FIT,
        verbose_name="Estado Médico",
    )
    injury_status = models.TextField(
        blank=True,
        verbose_name="Estado da Lesão",
        help_text="Descrição detalhada da lesão atual, se aplicável",
    )
    medical_clearance = models.BooleanField(
        default=False,
        verbose_name="Aptidão Médica",
        help_text="Se o jogador está medicamente apto para competir",
    )
    fitness_status = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Estado Físico",
        help_text="Avaliação geral da condição física",
    )
    medical_notes = models.TextField(
        blank=True,
        verbose_name="Notas Médicas",
        help_text="Observações médicas confidenciais (acesso restrito)",
    )

    # Medical Exam Dates
    last_medical_exam = models.DateField(
        null=True,
        blank=True,
        verbose_name="Último Exame Médico",
    )
    next_medical_exam = models.DateField(
        null=True,
        blank=True,
        verbose_name="Próximo Exame Médico",
    )

    # Emergency Medical Info
    allergies = models.TextField(
        blank=True,
        verbose_name="Alergias",
        help_text="Lista de alergias conhecidas",
    )
    current_medications = models.TextField(
        blank=True,
        verbose_name="Medicamentos Atuais",
        help_text="Medicamentos em uso",
    )
    medical_conditions = models.TextField(
        blank=True,
        verbose_name="Condições Médicas",
        help_text="Condições médicas pré-existentes",
    )

    class Meta:
        verbose_name = "Perfil Médico do Jogador"
        verbose_name_plural = "Perfis Médicos de Jogadores"

    def __str__(self) -> str:
        return f"Perfil Médico: {self.player.full_name}"

    @property
    def is_fit_to_play(self) -> bool:
        """Check if player is medically fit to play."""
        return (
            self.medical_status == self.MedicalStatus.FIT
            and self.medical_clearance is True
        )

    @property
    def needs_medical_exam(self) -> bool:
        """Check if player is due for a medical exam."""
        from datetime import date
        if not self.next_medical_exam:
            return False
        return self.next_medical_exam <= date.today()


class MedicalDocument(BaseModel):
    """Medical document for a player (e.g., medical certificate, scan results)."""

    class DocumentType(models.TextChoices):
        MEDICAL_CERTIFICATE = "medical_certificate", "Certificado Médico"
        INJURY_REPORT = "injury_report", "Relatório de Lesão"
        SCAN_RESULT = "scan_result", "Resultado de Exame"
        LAB_RESULT = "lab_result", "Resultado Laboratorial"
        VACCINATION_RECORD = "vaccination_record", "Registo de Vacinação"
        SURGERY_REPORT = "surgery_report", "Relatório de Cirurgia"
        PHYSICAL_EXAM = "physical_exam", "Exame Físico"
        CARDIAC_SCREENING = "cardiac_screening", "Rastreio Cardíaco"
        OTHER = "other", "Outro"

    class VerificationStatus(models.TextChoices):
        PENDING = "pending", "Pendente"
        VERIFIED = "verified", "Verificado"
        REJECTED = "rejected", "Rejeitado"
        EXPIRED = "expired", "Expirado"

    # Relations
    player = models.ForeignKey(
        "players.Player",
        on_delete=models.CASCADE,
        related_name="medical_documents",
        verbose_name="Jogador",
    )

    # Document Details
    document_type = models.CharField(
        max_length=30,
        choices=DocumentType.choices,
        default=DocumentType.OTHER,
        verbose_name="Tipo de Documento",
    )
    title = models.CharField(
        max_length=255,
        verbose_name="Título",
    )
    description = models.TextField(
        blank=True,
        verbose_name="Descrição",
    )

    # File
    file = models.ForeignKey(
        "media_assets.MediaAsset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="medical_documents",
        verbose_name="Ficheiro",
    )

    # Dates
    issued_at = models.DateField(
        verbose_name="Data de Emissão",
    )
    expires_at = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data de Validade",
    )

    # Verification
    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
        verbose_name="Estado de Verificação",
    )
    verified_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_medical_documents",
        verbose_name="Verificado Por",
    )
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data de Verificação",
    )

    # Access Control
    is_confidential = models.BooleanField(
        default=True,
        verbose_name="Confidencial",
        help_text="Se verdadeiro, apenas pessoal médico autorizado pode aceder",
    )

    class Meta:
        verbose_name = "Documento Médico"
        verbose_name_plural = "Documentos Médicos"
        ordering = ["-issued_at"]

    def __str__(self) -> str:
        return f"{self.title} - {self.player.full_name}"

    @property
    def is_valid(self) -> bool:
        """Check if document is valid (verified and not expired)."""
        from datetime import date
        if self.verification_status != self.VerificationStatus.VERIFIED:
            return False
        if self.expires_at and self.expires_at < date.today():
            return False
        return True

    @property
    def is_expired(self) -> bool:
        """Check if document is expired."""
        from datetime import date
        if not self.expires_at:
            return False
        return self.expires_at < date.today()
