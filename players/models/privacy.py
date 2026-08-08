from django.db import models
from common.models import BaseModel

VISIBILITY_CHOICES = [
    ("public", "Public"),
    ("club", "Club"),
    ("organization", "Organization"),
    ("agent", "Agent"),
    ("private", "Private"),
]


class PlayerPrivacySettings(BaseModel):
    player = models.OneToOneField(
        "players.Player", on_delete=models.CASCADE, related_name="privacy_settings"
    )

    profile_visibility = models.CharField(max_length=16, choices=VISIBILITY_CHOICES, default="public")
    contact_visibility = models.CharField(max_length=16, choices=VISIBILITY_CHOICES, default="club")
    contract_visibility = models.CharField(max_length=16, choices=VISIBILITY_CHOICES, default="club")
    salary_visibility = models.CharField(max_length=16, choices=VISIBILITY_CHOICES, default="private")
    medical_visibility = models.CharField(max_length=16, choices=VISIBILITY_CHOICES, default="private")
    documents_visibility = models.CharField(max_length=16, choices=VISIBILITY_CHOICES, default="club")
    statistics_visibility = models.CharField(max_length=16, choices=VISIBILITY_CHOICES, default="public")

    class Meta:
        verbose_name = "Player Privacy Settings"
        verbose_name_plural = "Player Privacy Settings"