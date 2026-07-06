from django.db import models
from common.models import BaseModel
from analytics.constants import ReportType, ReportStatus, ReportFormat


class GeneratedReport(BaseModel):
    """
    Represents a report generated (or requested to be generated) by a user.
    """

    tenant = models.ForeignKey(
        "core.Tenant",
        on_delete=models.CASCADE,
        related_name="generated_reports",
        null=True,
        blank=True,
        verbose_name="Tenant",
    )
    name = models.CharField(max_length=255, verbose_name="Report Name")
    report_type = models.CharField(
        max_length=50,
        choices=ReportType.CHOICES,
        verbose_name="Report Type",
    )
    status = models.CharField(
        max_length=20,
        choices=ReportStatus.CHOICES,
        default=ReportStatus.PENDING,
        verbose_name="Status",
    )
    format = models.CharField(
        max_length=10,
        choices=ReportFormat.CHOICES,
        verbose_name="Format",
    )
    filters = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Query Filters",
    )
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="generated_reports",
        verbose_name="Created By",
    )
    file = models.ForeignKey(
        "media_assets.MediaAsset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="generated_reports",
        verbose_name="Report File",
    )
    error_message = models.TextField(
        null=True,
        blank=True,
        verbose_name="Error Message",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Generated Report"
        verbose_name_plural = "Generated Reports"

    def __str__(self) -> str:
        tenant_name = self.tenant.name if self.tenant else "System Global"
        return f"{self.name} ({self.format}) - {tenant_name} - {self.status}"
