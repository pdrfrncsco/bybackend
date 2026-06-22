from django.db import models
from core.models import BaseModel, Tenant


class TenantSettings(BaseModel):
    tenant = models.OneToOneField(
        Tenant,
        on_delete=models.CASCADE,
        related_name='settings',
    )
    email_alerts = models.BooleanField(default=True)
    match_updates = models.BooleanField(default=True)
    marketing = models.BooleanField(default=False)
    financial_reports = models.BooleanField(default=True)

    def __str__(self):
        return f"Settings for {self.tenant.name}"
