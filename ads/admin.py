from django.contrib import admin

from .models import Advertisement


@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "client_name",
        "placement",
        "status",
        "tenant",
        "impressions",
        "clicks",
        "created_at",
    )
    list_filter = ("status", "placement", "tenant")
    search_fields = ("title", "client_name")
