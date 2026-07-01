"""
BOLAYETU — MatchEvent Serializers (Phase 4: Match Center)
"""

from rest_framework import serializers
from competitions.models import MatchEvent


class MatchEventSerializer(serializers.ModelSerializer):
    """Read serializer for a single match event (súmula)."""
    event_type_label = serializers.CharField(
        source="get_event_type_display", read_only=True
    )
    player_name = serializers.SerializerMethodField()
    player_off_name = serializers.SerializerMethodField()
    club_name = serializers.CharField(source="club.name", read_only=True)
    club_logo = serializers.SerializerMethodField()

    class Meta:
        model = MatchEvent
        fields = [
            "id",
            "event_type",
            "event_type_label",
            "minute",
            "extra_time",
            "player",
            "player_name",
            "player_off",
            "player_off_name",
            "club",
            "club_name",
            "club_logo",
            "notes",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_player_name(self, obj: MatchEvent) -> str | None:
        if obj.player:
            return obj.player.full_name
        return None

    def get_player_off_name(self, obj: MatchEvent) -> str | None:
        if obj.player_off:
            return obj.player_off.full_name
        return None

    def get_club_logo(self, obj: MatchEvent) -> str | None:
        if obj.club and obj.club.logo:
            return obj.club.logo
        return None


class MatchEventCreateSerializer(serializers.Serializer):
    """Write serializer for adding a new event to a match."""
    event_type = serializers.ChoiceField(choices=MatchEvent.EventType.choices)
    minute = serializers.IntegerField(min_value=0, max_value=120)
    extra_time = serializers.BooleanField(default=False)
    club = serializers.UUIDField()
    player = serializers.UUIDField(required=False, allow_null=True)
    player_off = serializers.UUIDField(required=False, allow_null=True)
    notes = serializers.CharField(max_length=255, required=False, default="")


class PlayerStatsSerializer(serializers.Serializer):
    """Serializer for per-player aggregated stats in a competition."""
    player_id = serializers.UUIDField()
    player__first_name = serializers.CharField()
    player__last_name = serializers.CharField()
    player__avatar = serializers.CharField(allow_null=True)
    club_id = serializers.UUIDField()
    club__name = serializers.CharField()
    goals = serializers.IntegerField()
    own_goals = serializers.IntegerField()
    yellow_cards = serializers.IntegerField()
    red_cards = serializers.IntegerField()
    appearances = serializers.IntegerField()
