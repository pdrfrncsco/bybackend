"""
BOLAYETU — Core Admin Configuration
"""

from django.contrib import admin

from core.models import Tenant


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ["name", "subdomain", "type", "status", "is_public", "is_verified", "created_at"]
    list_filter = ["type", "status", "is_public", "is_verified", "created_at"]
    search_fields = ["name", "slug", "email", "subdomain"]
    prepopulated_fields = {"slug": ("name",)}
    ordering = ["name"]
