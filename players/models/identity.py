from django.db import models
from common.models import BaseModel

DOCUMENT_TYPE_CHOICES = [
    ("national_id", "National ID"),
    ("passport", "Passport"),
    ("birth_certificate", "Birth Certificate"),
    ("residence_permit", "Residence Permit"),
    ("other", "Other"),
]

VERIFICATION_STATUS_CHOICES = [
    ("pending", "Pending"),
    ("verified", "Verified"),
    ("rejected", "Rejected"),
]


class PlayerIdentityDocument(BaseModel):
    """International identity documents for a Player."""

    player = models.ForeignKey(
        "players.Player",
        on_delete=models.CASCADE,
        related_name="identity_documents",
    )
    document_type = models.CharField(max_length=32, choices=DOCUMENT_TYPE_CHOICES)
    document_number = models.CharField(max_length=128)
    issuing_country = models.CharField(max_length=3, null=True, blank=True)
    issuing_authority = models.CharField(max_length=255, blank=True)
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)

    # Optional links to media assets (front/back scans)
    document_front = models.ForeignKey(
        "media_assets.MediaAsset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    document_back = models.ForeignKey(
        "media_assets.MediaAsset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    verification_status = models.CharField(
        max_length=16, choices=VERIFICATION_STATUS_CHOICES, default="pending"
    )
    verified_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True
    )
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Player Identity Document"
        verbose_name_plural = "Player Identity Documents"
        indexes = [models.Index(fields=["document_number"])]
