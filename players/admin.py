"""
BOLAYETU — Players Admin
"""

from django.contrib import admin

from players.models import (
    Player,
    PlayerRegistration,
    PlayerVideo,
    PlayerDocument,
    PlayerAchievement,
)


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


class PlayerVideoInline(admin.TabularInline):
    model = PlayerVideo
    extra = 0
    raw_id_fields = ("media_asset", "match")
    readonly_fields = ("id", "created_at", "updated_at")
    fields = ("title", "video_type", "status", "media_asset", "is_featured", "created_at")


class PlayerDocumentInline(admin.TabularInline):
    model = PlayerDocument
    extra = 0
    raw_id_fields = ("asset", "club", "uploaded_by")
    readonly_fields = ("id", "created_at", "updated_at", "verified_at")
    fields = ("title", "category", "status", "asset", "club", "is_private", "created_at")


class PlayerAchievementInline(admin.TabularInline):
    model = PlayerAchievement
    extra = 0
    readonly_fields = ("id", "created_at", "updated_at")
    fields = ("achievement_type", "title", "description", "date_achieved", "created_at")


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
    inlines = (
        PlayerRegistrationInline,
        PlayerVideoInline,
        PlayerDocumentInline,
        PlayerAchievementInline,
    )
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


@admin.register(PlayerVideo)
class PlayerVideoAdmin(admin.ModelAdmin):
    list_display = ("title", "player", "video_type", "status", "is_featured", "created_at")
    list_filter = ("video_type", "status", "is_featured", "created_at")
    search_fields = ("title", "description", "player__first_name", "player__last_name")
    readonly_fields = ("id", "created_at", "updated_at")
    raw_id_fields = ("player", "media_asset", "match")


@admin.register(PlayerDocument)
class PlayerDocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "player", "category", "status", "uploaded_by", "created_at")
    list_filter = ("category", "status", "is_private", "created_at")
    search_fields = ("title", "description", "player__first_name", "player__last_name")
    readonly_fields = ("id", "created_at", "updated_at", "verified_at")
    raw_id_fields = ("player", "asset", "club", "uploaded_by", "verified_by")


@admin.register(PlayerAchievement)
class PlayerAchievementAdmin(admin.ModelAdmin):
    list_display = ("title", "player", "achievement_type", "level", "date_achieved")
    list_filter = ("achievement_type", "level", "date_achieved")
    search_fields = ("title", "description", "player__first_name", "player__last_name")
    readonly_fields = ("id", "created_at", "updated_at")
    raw_id_fields = ("player", "competition", "club")
