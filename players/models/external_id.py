from django.db import models
from common.models import BaseModel


class PlayerExternalId(BaseModel):
    player = models.ForeignKey(
        "players.Player", on_delete=models.CASCADE, related_name="external_ids"
    )
    system = models.CharField(max_length=64)
    external_id = models.CharField(max_length=128)
    issued_at = models.DateField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "Player External ID"
        verbose_name_plural = "Player External IDs"
        indexes = [models.Index(fields=["system", "external_id"]) ]
