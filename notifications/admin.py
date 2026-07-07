from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "type", "recipient", "status", "created_at")
    list_filter = ("type", "status")
    readonly_fields = ("created_at", "delivered_at")
