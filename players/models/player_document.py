"""
BOLAYETU — PlayerDocument Model

Represents a document uploaded for a player and stored via the DAM.

Architecture:
    - PlayerDocument is a GLOBAL entity — linked to a Player (not tenant-scoped).
    - Uses MediaAsset for actual file storage via DAM integration.
    - Supports multiple document categories: contracts, passport, medical certificates, etc.
"""

from django.conf import settings
from django.db import models

from common.models import BaseModel


class PlayerDocument(BaseModel):
    """
    Represents a document associated with a player profile.
    
    Documents can be:
        - Contracts (player agreements with clubs)
        - Passport/ID (identification documents)
        - Medical certificates (fitness, health records)
        - Licenses (player licenses, registrations)
        - Certificates (coaching badges, educational)
        - Other documents
    
    The actual document file is stored via MediaAsset (DAM integration).
    """

    class DocumentCategory(models.TextChoices):
        CONTRACT = "contract", "Contrato"
        PASSPORT = "passport", "Passaporte/Bilhete de Identidade"
        MEDICAL = "medical", "Certificado Médico"
        LICENSE = "license", "Licença de Jogador"
        CERTIFICATE = "certificate", "Certificado"
        TRANSFER = "transfer", "Documento de Transferência"
        INSURANCE = "insurance", "Seguro"
        OTHER = "other", "Outro"

    class DocumentStatus(models.TextChoices):
        PENDING = "pending", "Pendente"
        VERIFIED = "verified", "Verificado"
        REJECTED = "rejected", "Rejeitado"
        EXPIRED = "expired", "Expirado"

    # Player reference (global entity)
    player = models.ForeignKey(
        "players.Player",
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name="Player",
    )

    # Document metadata
    title = models.CharField(
        max_length=255,
        verbose_name="Title",
        help_text="Document title (e.g., 'Contrato com Petro de Luanda - 2025')",
    )
    category = models.CharField(
        max_length=20,
        choices=DocumentCategory.choices,
        default=DocumentCategory.OTHER,
        verbose_name="Category",
    )
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name="Description",
        help_text="Optional description or notes about the document",
    )

    # DAM integration — link to MediaAsset for uploaded documents
    asset = models.ForeignKey(
        "media_assets.MediaAsset",
        on_delete=models.CASCADE,
        related_name="player_documents",
        verbose_name="Media Asset",
        help_text="Uploaded document file via DAM",
    )

    # Document validity and verification
    status = models.CharField(
        max_length=20,
        choices=DocumentStatus.choices,
        default=DocumentStatus.PENDING,
        verbose_name="Status",
    )
    valid_from = models.DateField(
        null=True,
        blank=True,
        verbose_name="Valid From",
    )
    valid_until = models.DateField(
        null=True,
        blank=True,
        verbose_name="Valid Until",
    )

    # Club context (optional) — for club-specific documents like contracts
    club = models.ForeignKey(
        "clubs.Club",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="player_documents",
        verbose_name="Related Club",
        help_text="Club this document is associated with (e.g., for contracts)",
    )

    # Visibility and access control
    is_private = models.BooleanField(
        default=True,
        verbose_name="Is Private",
        help_text="Private documents are only visible to authorized users",
    )

    # Upload metadata
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="player_documents_uploaded",
        verbose_name="Uploaded By",
    )

    # Verification metadata
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="player_documents_verified",
        verbose_name="Verified By",
    )
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Verified At",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Player Document"
        verbose_name_plural = "Player Documents"
        indexes = [
            models.Index(fields=["player", "category"]),
            models.Index(fields=["player", "status"]),
            models.Index(fields=["valid_until"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["player", "title"],
                name="unique_player_document_title_per_player",
            )
        ]

    def __str__(self) -> str:
        return f"{self.title} — {self.player.full_name}"

    @property
    def is_valid(self) -> bool:
        """Check if document is currently valid."""
        from datetime import date
        today = date.today()
        
        if self.status != self.DocumentStatus.VERIFIED:
            return False
        
        if self.valid_from and self.valid_from > today:
            return False
        
        if self.valid_until and self.valid_until < today:
            return False
        
        return True

    def verify(self, user: settings.AUTH_USER_MODEL) -> None:
        """Mark document as verified."""
        from django.utils import timezone
        self.status = self.DocumentStatus.VERIFIED
        self.verified_by = user
        self.verified_at = timezone.now()
        self.save(update_fields=["status", "verified_by", "verified_at"])

    def reject(self) -> None:
        """Mark document as rejected."""
        self.status = self.DocumentStatus.REJECTED
        self.save(update_fields=["status"])
