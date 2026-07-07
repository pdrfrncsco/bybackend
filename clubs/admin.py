"""
BOLAYETU — Clubs Admin
"""

from django.contrib import admin

from clubs.models import (
    Club,
    ClubMember,
    ClubAffiliationRequest,
    ClubDocument,
    ClubSponsor,
    Transfer,
)


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


@admin.register(ClubAffiliationRequest)
class ClubAffiliationRequestAdmin(admin.ModelAdmin):
    list_display = ("club","status")
    list_filter = ("status", "club__tenant")
    search_fields = ("club__name", "email")
    raw_id_fields = ("club",)


@admin.register(ClubDocument)
class ClubDocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "club", "category", "uploaded_by", "created_at")
    list_filter = ("category", "is_public", "created_at")
    search_fields = ("title", "club__name", "uploaded_by__email")
    readonly_fields = ("id", "created_at", "updated_at")
    raw_id_fields = ("club", "tenant", "asset", "uploaded_by")


@admin.register(ClubSponsor)
class ClubSponsorAdmin(admin.ModelAdmin):
    list_display = ("name", "club", "sponsor_type", "is_active", "sort_order")
    list_filter = ("sponsor_type", "is_active")
    search_fields = ("name", "club__name")
    readonly_fields = ("id", "created_at", "updated_at")
    raw_id_fields = ("club", "tenant", "logo_asset", "uploaded_by")



@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = ("player", "from_club", "to_club", "transfer_type", "status", "transfer_date")
    list_filter = ("transfer_type", "status", "transfer_date", "tenant")
    search_fields = ("player__first_name", "player__last_name", "from_club__name", "to_club__name")
    readonly_fields = ("id", "created_at", "updated_at", "approved_at", "completed_at", "cancelled_at")
    raw_id_fields = ("tenant", "player", "from_club", "to_club")
    actions = ("approve_transfer", "cancel_transfer", "complete_transfer")
