from django.db import models
from common.models import BaseModel

CONSENT_STATUS_CHOICES = [
    ("pending", "Pending"),
    ("given", "Given"),
    ("revoked", "Revoked"),
]


class LegalGuardian(BaseModel):
    player = models.ForeignKey(
        "players.Player", on_delete=models.CASCADE, related_name="legal_guardians"
    )
    name = models.CharField(max_length=255)
    relationship = models.CharField(max_length=100)
    document_number = models.CharField(max_length=128, null=True, blank=True)
    phone = models.CharField(max_length=30)
    email = models.EmailField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)

    consent_status = models.CharField(max_length=16, choices=CONSENT_STATUS_CHOICES, default="pending")
    consent_document = models.ForeignKey(
        "media_assets.MediaAsset", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    consent_given_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Legal Guardian"
        verbose_name_plural = "Legal Guardians"