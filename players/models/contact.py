from django.db import models
from common.models import BaseModel


class PlayerContact(BaseModel):
    player = models.OneToOneField(
        "players.Player",
        on_delete=models.CASCADE,
        related_name="contact",
    )

    primary_email = models.EmailField()
    secondary_email = models.EmailField(null=True, blank=True)
    mobile_phone = models.CharField(max_length=30, null=True, blank=True)
    secondary_phone = models.CharField(max_length=30, null=True, blank=True)
    country_code = models.CharField(max_length=5, null=True, blank=True)

    address = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    province = models.CharField(max_length=100, null=True, blank=True)
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    country = models.CharField(max_length=3, null=True, blank=True)

    class Meta:
        verbose_name = "Player Contact"
        verbose_name_plural = "Player Contacts"


class EmergencyContact(BaseModel):
    player = models.ForeignKey(
        "players.Player", on_delete=models.CASCADE, related_name="emergency_contacts"
    )
    name = models.CharField(max_length=255)
    relationship = models.CharField(max_length=100)
    phone = models.CharField(max_length=30)
    email = models.EmailField(null=True, blank=True)
    country = models.CharField(max_length=3, null=True, blank=True)

    class Meta:
        verbose_name = "Emergency Contact"
        verbose_name_plural = "Emergency Contacts"