from django.conf import settings
from django.db import models
from common.models import BaseModel


class MatchClockAction(BaseModel):
    """Immutable audit record for a MatchCenter clock command."""

    match = models.ForeignKey("competitions.Match", on_delete=models.CASCADE, related_name="clock_actions")
    tenant = models.ForeignKey("core.Tenant", on_delete=models.CASCADE, related_name="match_clock_actions")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="match_clock_actions")
    action = models.CharField(max_length=64)
    status_before = models.CharField(max_length=20, blank=True, default="")
    status_after = models.CharField(max_length=20, blank=True, default="")
    period_before = models.CharField(max_length=32, blank=True, default="")
    period_after = models.CharField(max_length=32, blank=True, default="")
    minute_before = models.PositiveSmallIntegerField(default=0)
    minute_after = models.PositiveSmallIntegerField(default=0)
    clock_version = models.PositiveIntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Match Clock Action"
        verbose_name_plural = "Match Clock Actions"

    def __str__(self):
        return f"{self.match_id} · {self.action} · {self.created_at}"
