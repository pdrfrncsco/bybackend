"""
BOLAYETU — Fair Play & Ranking Serializers

Serializers for PlayerSuspension and CompetitionRanking endpoints.
"""

from rest_framework import serializers
from competitions.models import PlayerSuspension, CompetitionRanking


class PlayerSuspensionSerializer(serializers.ModelSerializer):
    """Serializer for PlayerSuspension model."""
    
    player_name = serializers.CharField(source="player.full_name", read_only=True)
    club_name = serializers.CharField(source="club.name", read_only=True)
    competition_name = serializers.CharField(source="competition.name", read_only=True)
    suspension_type_display = serializers.CharField(
        source="get_suspension_type_display", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    remaining_matches = serializers.IntegerField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = PlayerSuspension
        fields = [
            "id",
            "player",
            "player_name",
            "club",
            "club_name",
            "competition",
            "competition_name",
            "suspension_type",
            "suspension_type_display",
            "matches_suspended",
            "matches_served",
            "remaining_matches",
            "status",
            "status_display",
            "is_active",
            "effective_from",
            "effective_until",
            "served_on",
            "reason",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "matches_served",
            "served_on",
            "created_at",
            "updated_at",
        ]


class CreateSuspensionSerializer(serializers.ModelSerializer):
    """Serializer for creating manual suspensions."""
    
    class Meta:
        model = PlayerSuspension
        fields = [
            "player",
            "club",
            "competition",
            "suspension_type",
            "matches_suspended",
            "effective_from",
            "reason",
        ]


class CompetitionRankingSerializer(serializers.ModelSerializer):
    """Serializer for CompetitionRanking model."""
    
    player_name = serializers.CharField(source="player.full_name", read_only=True)
    club_name = serializers.CharField(source="club.name", read_only=True)
    ranking_type_display = serializers.CharField(
        source="get_ranking_type_display", read_only=True
    )
    aggregation_level_display = serializers.CharField(
        source="get_aggregation_level_display", read_only=True
    )
    position_change = serializers.IntegerField(read_only=True)
    moved_up = serializers.BooleanField(read_only=True)
    moved_down = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = CompetitionRanking
        fields = [
            "id",
            "player",
            "player_name",
            "club",
            "club_name",
            "competition",
            "ranking_type",
            "ranking_type_display",
            "aggregation_level",
            "aggregation_level_display",
            "season",
            "month",
            "year",
            "position",
            "previous_position",
            "position_change",
            "moved_up",
            "moved_down",
            "value",
            "stats",
            "is_official",
            "last_updated",
        ]
        read_only_fields = [
            "id",
            "position",
            "previous_position",
            "last_updated",
        ]


class PlayerEligibilitySerializer(serializers.Serializer):
    """Serializer for player eligibility check response."""
    
    player_id = serializers.UUIDField()
    player_name = serializers.CharField()
    competition_id = serializers.UUIDField()
    is_eligible = serializers.BooleanField()
    reason = serializers.CharField(allow_null=True)
    active_suspensions = PlayerSuspensionSerializer(many=True)


class FairPlayRankingSerializer(serializers.Serializer):
    """Serializer for fair play ranking response."""
    
    position = serializers.IntegerField()
    club_id = serializers.UUIDField()
    club_name = serializers.CharField()
    yellow_cards = serializers.IntegerField()
    yellow_reds = serializers.IntegerField()
    red_cards = serializers.IntegerField()
    fair_play_score = serializers.IntegerField()


class TopScorerSerializer(serializers.Serializer):
    """Serializer for top scorers ranking response."""
    
    position = serializers.IntegerField()
    player_id = serializers.UUIDField()
    player_name = serializers.CharField()
    goals = serializers.IntegerField()
    club_name = serializers.CharField(allow_null=True)
    season = serializers.CharField()
