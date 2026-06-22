from django.contrib import admin
from .models import ReportJob


@admin.register(ReportJob)
class ReportJobAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "tenant",
        "user",
        "report_type",
        "format",
        "status",
        "created_at",
        "file",
    )
    list_filter = (
        "status",
        "format",
        "report_type",
        "tenant",
        "user",
        "created_at",
    )
    search_fields = (
        "id",
        "user__email",
        "user__username",
        "tenant__name",
        "report_type",
    )
    readonly_fields = ("created_at", "updated_at", "error_message")
