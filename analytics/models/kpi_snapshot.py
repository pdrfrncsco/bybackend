from django.db import models
from common.models import BaseModel
from analytics.constants import MetricKey


class KPISnapshot(BaseModel):
    """
    Caches calculated KPIs/Metrics for a given tenant on a specific date.
    This avoids recalculating heavy aggregates in real-time.
    """

    tenant = models.ForeignKey(
        "core.Tenant",
        on_delete=models.CASCADE,
        related_name="kpi_snapshots",
        null=True,
        blank=True,
        verbose_name="Tenant",
    )
    date = models.DateField(verbose_name="Snapshot Date")
    metric_key = models.CharField(
        max_length=100,
        choices=MetricKey.CHOICES,
        verbose_name="Metric Key",
    )
    value = models.FloatField(verbose_name="Metric Value")

    class Meta:
        ordering = ["-date", "metric_key"]
        unique_together = ("tenant", "date", "metric_key")
        verbose_name = "KPI Snapshot"
        verbose_name_plural = "KPI Snapshots"

    def __str__(self) -> str:
        tenant_name = self.tenant.name if self.tenant else "System Global"
        return f"{tenant_name} - {self.date} - {self.metric_key}: {self.value}"
