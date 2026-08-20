from django.contrib import admin
from competitions.models import (
    Competition,
    CompetitionRegistration,
    CompetitionRanking,
    CompetitionRegulation,
    Match,
    MatchEvent,
    MatchLineup,
    LineupSubmission,
    MatchReport,
    Goal,
    MatchStats,
    Standing,
    PlayerSuspension,
    TacticalPositions,
)

@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ("name", "competition_type", "season", "status", "tenant")
    list_filter = ("status", "competition_type", "season")
    search_fields = ("name", "tenant__name")
    readonly_fields = ("created_at", "updated_at")

@admin.register(CompetitionRegistration)
class CompetitionRegistrationAdmin(admin.ModelAdmin):
    list_display = ("competition", "club", "tenant", "created_at")
    list_filter = ("competition",)
    search_fields = ("club__name", "competition__name")
    readonly_fields = ("created_at", "updated_at")

@admin.register(CompetitionRanking)
class CompetitionRankingAdmin(admin.ModelAdmin):
    list_display = ("player", "club", "ranking_type", "position", "value")
    list_filter = ("ranking_type", "aggregation_level")
    search_fields = ("player__first_name", "player__last_name", "club__name")
    readonly_fields = ("created_at",)

@admin.register(CompetitionRegulation)
class CompetitionRegulationAdmin(admin.ModelAdmin):
    list_display = ("competition", "status", "created_at")
    list_filter = ("status", "competition")
    search_fields = ("competition__name",)
    readonly_fields = ("created_at", "updated_at")

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ("__str__", "match_date", "status", "current_period", "current_minute", "phase", "tenant")
    list_filter = ("status", "current_period", "competition", "phase")
    search_fields = ("home_club__name", "away_club__name", "competition__name")
    date_hierarchy = "match_date"
    list_select_related = ("competition", "home_club", "away_club", "tenant")
    ordering = ("-match_date", "round_number")
    readonly_fields = ("created_at", "updated_at")

@admin.register(MatchEvent)
class MatchEventAdmin(admin.ModelAdmin):
    list_display = ("__str__", "match", "event_type", "minute", "extra_time", "club", "player", "idempotency_key")
    list_filter = ("event_type", "extra_time", "match__status", "match__competition")
    search_fields = (
        "idempotency_key", "player__first_name", "player__last_name",
        "club__name", "match__home_club__name", "match__away_club__name",
    )
    list_select_related = ("match", "club", "player", "player_off", "tenant")
    ordering = ("-created_at", "-minute")
    readonly_fields = ("created_at", "updated_at")

    # Event creation/removal must go through MatchEventService so score,
    # player stats, notifications and domain events stay consistent.
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return request.method in ("GET", "HEAD")

@admin.register(MatchLineup)
class MatchLineupAdmin(admin.ModelAdmin):
    list_display = ("player", "match", "club", "status", "position", "shirt_number")
    list_filter = ("status", "position", "match__competition")
    search_fields = ("player__first_name", "player__last_name", "club__name")
    readonly_fields = ("created_at", "updated_at")

@admin.register(LineupSubmission)
class LineupSubmissionAdmin(admin.ModelAdmin):
    list_display = ("match", "club", "status", "submitted_at", "formation")
    list_filter = ("status", "match__competition")
    search_fields = ("club__name", "match__home_club__name", "match__away_club__name")
    readonly_fields = ("created_at", "updated_at", "submitted_at")
    list_select_related = ("match", "club", "submitted_by", "confirmed_by")

@admin.register(MatchReport)
class MatchReportAdmin(admin.ModelAdmin):
    list_display = ("match", "status", "home_score", "away_score", "generated_at")
    list_filter = ("status", "match__competition")
    search_fields = ("match__home_club__name", "match__away_club__name")
    readonly_fields = (
        "created_at", "updated_at", "generated_at", "finalized_at",
        "requested_at", "requested_by", "finalized_by", "generated_by",
    )
    list_select_related = ("match", "match__competition")

@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ("player", "match", "minute", "goal_type", "club")
    list_filter = ("goal_type", "match__competition")
    search_fields = ("player__first_name", "player__last_name", "match__home_club__name", "match__away_club__name")
    readonly_fields = ("created_at",)

@admin.register(MatchStats)
class MatchStatsAdmin(admin.ModelAdmin):
    list_display = ("match", "club", "possession", "shots_on_goal", "shots_off_goal")
    list_filter = ("match__competition",)
    search_fields = ("club__name",)
    readonly_fields = ("created_at", "updated_at")
    list_select_related = ("match", "club")

@admin.register(Standing)
class StandingAdmin(admin.ModelAdmin):
    list_display = ("club", "competition", "phase", "group_id", "position", "points", "played")
    list_filter = ("competition",)
    search_fields = ("club__name", "competition__name")
    readonly_fields = ("created_at", "updated_at")

@admin.register(PlayerSuspension)
class PlayerSuspensionAdmin(admin.ModelAdmin):
    list_display = ("player", "competition", "suspension_type", "status", "matches_suspended", "matches_served")
    list_filter = ("suspension_type", "status", "competition")
    search_fields = ("player__first_name", "player__last_name", "competition__name")
    readonly_fields = ("created_at", "updated_at")


@admin.register(TacticalPositions)
class TacticalPositionsAdmin(admin.ModelAdmin):
    list_display = ("match", "club", "version", "updated_at", "tenant")
    list_filter = ("match__competition",)
    search_fields = ("club__name", "match__home_club__name", "match__away_club__name")
    list_select_related = ("match", "club", "tenant")
    readonly_fields = ("created_at", "updated_at", "version")
