"""
BOLAYETU — Fans App Admin Configuration
"""

from django.contrib import admin
from .models import FanProfile, FanFollow, MatchPrediction, FanMVPVote


@admin.register(FanProfile)
class FanProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "favorite_club", "points", "correct_predictions_count", "total_predictions_count", "created_at")
    search_fields = ("user__email", "user__username", "user__first_name", "user__last_name", "favorite_club__name")
    list_filter = ("notification_match_start", "notification_goals", "created_at")
    readonly_fields = ("created_at", "updated_at")


@admin.register(FanFollow)
class FanFollowAdmin(admin.ModelAdmin):
    list_display = ("user", "target_type", "club", "player", "competition", "created_at")
    search_fields = ("user__email", "club__name", "player__first_name", "player__last_name", "competition__name")
    list_filter = ("target_type", "created_at")


@admin.register(MatchPrediction)
class MatchPredictionAdmin(admin.ModelAdmin):
    list_display = ("user", "match", "predicted_home_score", "predicted_away_score", "status", "points_awarded", "created_at")
    search_fields = ("user__email", "match__home_club__name", "match__away_club__name")
    list_filter = ("status", "points_awarded", "created_at")


@admin.register(FanMVPVote)
class FanMVPVoteAdmin(admin.ModelAdmin):
    list_display = ("user", "match", "player", "created_at")
    search_fields = ("user__email", "player__first_name", "player__last_name")
    list_filter = ("created_at",)
