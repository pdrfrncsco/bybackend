"""
BOLAYETU — Transfer Admin

Admin configuration for Transfer model.
"""

from django.contrib import admin
from transfers.models import Transfer


@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    """Admin interface for Transfer model."""

    list_display = [
        "player",
        "from_club",
        "to_club",
        "status",
        "joined_date",
        "fee",
        "request_date",
    ]
    list_filter = ["status", "joined_date"]
    search_fields = [
        "player__first_name",
        "player__last_name",
        "from_club__name",
        "to_club__name",
    ]
    raw_id_fields = ["player", "from_club", "to_club", "competition"]
    date_hierarchy = "request_date"
    ordering = ["-request_date"]

    fieldsets = (
        ("Player Information", {
            "fields": ("player",)
        }),
        ("Transfer Details", {
            "fields": (
                "from_club",
                "from_tenant",
                "to_club",
                "to_tenant",
                "competition",
            )
        }),
        ("Registration Details", {
            "fields": ("joined_date", "shirt_number", "fee")
        }),
        ("Status", {
            "fields": (
                "status",
                "request_date",
                "completed_date",
                "rejection_reason",
            )
        }),
    )

    readonly_fields = ["request_date", "completed_date"]
