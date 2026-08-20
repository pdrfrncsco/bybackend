from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "type", "recipient", "status", "created_at")
    list_filter = ("type", "status")
    search_fields = ("type", "tenant_id", "recipient__email")
    list_select_related = ("recipient",)
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "delivered_at")
    fieldsets = (
        ("Delivery", {"fields": ("recipient", "tenant_id", "type", "status", "delivered_at")} ),
        ("Payload", {"fields": ("payload",)}),
        ("Audit", {"fields": ("created_at",)}),
    )
