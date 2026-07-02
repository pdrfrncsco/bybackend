"""
BOLAYETU — Players Admin
"""

from django.contrib import admin

from players.models import Player, PlayerRegistration


class PlayerRegistrationInline(admin.TabularInline):
    model = PlayerRegistration
    extra = 0
    raw_id_fields = ("club", "competition", "tenant")
    readonly_fields = ("id", "created_at", "updated_at")
    fields = (
        "club",
        "competition",
        "tenant",
        "shirt_number",
        "joined_date",
        "left_date",
        "status",
        "matches_played",
        "goals",
        "assists",
    )


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "slug",
        "primary_position",
        "status",
        "nationality",
        "email",
        "user",
    )
    list_filter = ("status", "primary_position", "nationality", "foot")
    search_fields = ("first_name", "last_name", "slug", "email", "phone")
    readonly_fields = (
        "id",
        "slug",
        "created_at",
        "updated_at",
        "total_matches",
        "total_goals",
        "total_assists",
    )
    raw_id_fields = ("user",)
    inlines = (PlayerRegistrationInline,)
    fieldsets = (
        (
            "Personal Information",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "slug",
                    "email",
                    "phone",
                )
            },
        ),
        (
            "Physical",
            {
                "fields": (
                    "date_of_birth",
                    "nationality",
                    "height_cm",
                    "weight_kg",
                    "foot",
                )
            },
        ),
        (
            "Football",
            {
                "fields": (
                    "primary_position",
                    "shirt_number",
                )
            },
        ),
        (
            "Profile",
            {
                "fields": (
                    "bio",
                    "avatar",
                )
            },
        ),
        (
            "Status & Account",
            {
                "fields": (
                    "status",
                    "user",
                )
            },
        ),
        (
            "Career Statistics",
            {
                "fields": (
                    "total_matches",
                    "total_goals",
                    "total_assists",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "id",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )


@admin.register(PlayerRegistration)
class PlayerRegistrationAdmin(admin.ModelAdmin):
    list_display = (
        "player",
        "club",
        "competition",
        "tenant",
        "shirt_number",
        "joined_date",
        "left_date",
        "status",
    )
    list_filter = ("status", "tenant", "joined_date")
    search_fields = (
        "player__first_name",
        "player__last_name",
        "club__name",
        "competition__name",
    )
    readonly_fields = ("id", "created_at", "updated_at")
    raw_id_fields = ("player", "club", "competition", "tenant")
    date_hierarchy = "joined_date"
    fieldsets = (
        (
            "Registration",
            {
                "fields": (
                    "player",
                    "club",
                    "competition",
                    "tenant",
                )
            },
        ),
        (
            "Details",
            {
                "fields": (
                    "shirt_number",
                    "joined_date",
                    "left_date",
                    "status",
                )
            },
        ),
        (
            "Statistics",
            {
                "fields": (
                    "matches_played",
                    "goals",
                    "assists",
                    "yellow_cards",
                    "red_cards",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "id",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )
