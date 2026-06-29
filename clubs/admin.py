"""
BOLAYETU — Clubs Admin
"""

from django.contrib import admin

from clubs.models import Club, ClubMember


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "tenant", "status", "is_public", "city", "country")
    list_filter = ("status", "is_public", "is_verified", "tenant")
    search_fields = ("name", "slug", "short_name", "city")
    readonly_fields = ("id", "slug", "created_at", "updated_at")
    raw_id_fields = ("tenant",)


@admin.register(ClubMember)
class ClubMemberAdmin(admin.ModelAdmin):
    list_display = ("display_name", "club", "role", "jersey_number", "position", "is_active")
    list_filter = ("role", "is_active", "position", "club__tenant")
    search_fields = ("full_name", "user__email", "club__name")
    readonly_fields = ("id", "created_at", "updated_at")
    raw_id_fields = ("user", "club")
