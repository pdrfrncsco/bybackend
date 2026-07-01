from django.contrib import admin
from competitions.models import (
    Competition,
    CompetitionRegistration,
    Match,
    MatchEvent,
    Standing,
)

@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ("name", "competition_type", "season", "status", "tenant")
    list_filter = ("status", "competition_type", "season")
    search_fields = ("name", "tenant__name")

@admin.register(CompetitionRegistration)
class CompetitionRegistrationAdmin(admin.ModelAdmin):
    list_display = ("competition", "club", "tenant", "created_at")
    list_filter = ("competition",)
    search_fields = ("club__name", "competition__name")

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ("__str__", "match_date", "status", "tenant")
    list_filter = ("status", "competition")
    search_fields = ("home_club__name", "away_club__name", "competition__name")

@admin.register(MatchEvent)
class MatchEventAdmin(admin.ModelAdmin):
    list_display = ("__str__", "match", "event_type", "minute", "player")
    list_filter = ("event_type", "match__competition")
    search_fields = ("player__first_name", "player__last_name", "match__home_club__name", "match__away_club__name")

@admin.register(Standing)
class StandingAdmin(admin.ModelAdmin):
    list_display = ("club", "competition", "position", "points", "played")
    list_filter = ("competition",)
    search_fields = ("club__name", "competition__name")
