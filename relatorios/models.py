from django.db import models
from django.conf import settings

from core.models import BaseModel, Tenant


class ReportJob(BaseModel):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    )

    FORMAT_CHOICES = (
        ("pdf", "PDF"),
        ("csv", "CSV"),
        ("excel", "Excel"),
    )

    REPORT_TYPE_CHOICES = (
        ("standings", "Standings / Classificação"),
        ("club_performance", "Desempenho por Clube"),
        ("player_stats", "Estatísticas de Jogadores"),
        ("individual_technical_sheet", "Ficha Técnica Individual"),
        ("calendar", "Calendário de Jogos"),
        ("squad_list", "Lista de Jogadores"),
        ("match_sheet", "Ficha de Jogo"),
    )

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="report_jobs",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="report_jobs",
    )
    report_type = models.CharField(
        max_length=64,
        choices=REPORT_TYPE_CHOICES,
    )
    format = models.CharField(
        max_length=16,
        choices=FORMAT_CHOICES,
        default="pdf",
    )
    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default="pending",
    )
    params = models.JSONField(default=dict, blank=True)
    file = models.FileField(
        upload_to="reports/",
        null=True,
        blank=True,
    )
    error_message = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.report_type} ({self.format}) - {self.status}"
