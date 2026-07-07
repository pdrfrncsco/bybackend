"""
BOLAYETU — Analytics Admin Interface

Registers KPISnapshot and GeneratedReport models with the Django Admin site.
"""

from django.contrib import admin

from analytics.models import KPISnapshot, GeneratedReport


@admin.register(KPISnapshot)
class KPISnapshotAdmin(admin.ModelAdmin):
    list_display = ("date", "tenant", "metric_key", "value", "created_at")
    list_filter = ("metric_key", "date", "tenant")
    search_fields = ("metric_key", "tenant__name")
    readonly_fields = ("id", "created_at", "updated_at")
    raw_id_fields = ("tenant",)


@admin.register(GeneratedReport)
class GeneratedReportAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "tenant",
        "report_type",
        "status",
        "format",
        "created_by",
        "created_at",
    )
    list_filter = ("report_type", "status", "format", "tenant", "created_at")
    search_fields = ("name", "tenant__name", "created_by__email")
    readonly_fields = ("id", "error_message", "created_at", "updated_at")
    raw_id_fields = ("tenant", "created_by", "file")
