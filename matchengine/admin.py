from django.contrib import admin
from .models import MatchEvent, MatchStats, MatchLineupEntry


@admin.register(MatchEvent)
class MatchEventAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "match",
        "tenant",
        "type",
        "team",
        "player",
        "secondary_player",
        "minute",
        "is_own_goal",
        "created_at",
    )
    list_filter = (
        "tenant",
        "type",
        "team",
        "player",
        "is_own_goal",
        "minute",
    )
    search_fields = (
        "id",
        "match__id",
        "team__name",
        "player__name",
        "secondary_player__name",
    )
    list_select_related = ("tenant", "match", "team", "player", "secondary_player")
    ordering = ("-created_at",)


@admin.register(MatchStats)
class MatchStatsAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "match",
        "tenant",
        "home_possession",
        "away_possession",
        "home_shots",
        "away_shots",
        "home_corners",
        "away_corners",
        "home_fouls",
        "away_fouls",
    )
    list_filter = ("tenant", "match")
    search_fields = ("id", "match__id")
    list_select_related = ("tenant", "match")


@admin.register(MatchLineupEntry)
class MatchLineupEntryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "match",
        "tenant",
        "team",
        "player",
        "number",
        "position",
        "is_starter",
        "is_captain",
    )
    list_filter = (
        "tenant",
        "match",
        "team",
        "position",
        "is_starter",
        "is_captain",
    )
    search_fields = (
        "id",
        "match__id",
        "team__name",
        "player__name",
    )
    list_select_related = ("tenant", "match", "team", "player")
