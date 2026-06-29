"""
BOLAYETU — Organizations Admin
"""

from django.contrib import admin

from organizations.models import OrganizationSubscription


@admin.register(OrganizationSubscription)
class OrganizationSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "tenant", "is_active", "subscribed_at")
    list_filter = ("is_active",)
    search_fields = ("user__email", "tenant__name")
    readonly_fields = ("id", "subscribed_at")
