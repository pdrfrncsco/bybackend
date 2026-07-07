"""
BOLAYETU — Lineup & Report Serializers

DRF serializers for match lineups, lineup submissions, and match reports.
"""

from rest_framework import serializers
from django.db import transaction

from players.models import Player
from clubs.models import Club
from competitions.models import (
    MatchLineup, LineupSubmission, MatchReport,
    Goal, MatchStats
)
from competitions.services.lineup_service import (
    LineupService, LineupValidationError, PlayerNotEligible,
    LineupAlreadySubmitted
)


# ─── Player Serializers ─────────────────────────────────────────────────────


class PlayerBasicSerializer(serializers.ModelSerializer):
    """Basic player info for lineup display."""

    class Meta:
        model = Player
        fields = ['id', 'full_name', 'position', 'date_of_birth', 'nationality']
        read_only_fields = fields


# ─── Match Lineup Serializers ──────────────────────────────────────────────


class MatchLineupPlayerSerializer(serializers.ModelSerializer):
    """Nested player in lineup entry."""
    
    player = PlayerBasicSerializer(read_only=True)
    position_display = serializers.CharField(
        source='get_position_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )

    class Meta:
        model = MatchLineup
        fields = [
            'id', 'player', 'player_id', 'status', 'status_display',
            'position', 'position_display', 'shirt_number',
            'is_captain', 'is_goalkeeper', 'formation_position',
            'minutes_played', 'substituted_in_minute',
            'substituted_out_minute'
        ]
        read_only_fields = ['id', 'player', 'minutes_played']


class MatchLineupInputSerializer(serializers.Serializer):
    """Serializer for submitting player in lineup."""

    player_id = serializers.UUIDField()
    status = serializers.ChoiceField(
        choices=['starter', 'substitute'],
        required=True
    )
    position = serializers.CharField(max_length=3)
    shirt_number = serializers.IntegerField(min_value=1, max_value=99)
    is_captain = serializers.BooleanField(required=False, default=False)
    is_goalkeeper = serializers.BooleanField(required=False, default=False)
    formation_position = serializers.IntegerField(
        min_value=1, max_value=11,
        required=False,
        allow_null=True
    )


# ─── Lineup Submission Serializers ─────────────────────────────────────────


class LineupSubmissionSerializer(serializers.ModelSerializer):
    """Lineup submission with full details."""

    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    lineup_players = MatchLineupPlayerSerializer(
        source='lineup_entries',
        many=True,
        read_only=True
    )

    class Meta:
        model = LineupSubmission
        fields = [
            'id', 'match', 'club', 'formation', 'status', 'status_display',
            'submitted_at', 'submitted_by', 'confirmed_at', 'locked_at',
            'lineup_players', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'match', 'club', 'submitted_at', 'confirmed_at',
            'locked_at', 'lineup_players', 'created_at', 'updated_at'
        ]


class LineupSubmissionInputSerializer(serializers.Serializer):
    """Serializer for submitting a complete lineup."""

    formation = serializers.CharField(max_length=50, required=False)
    players = MatchLineupInputSerializer(many=True, required=True)

    def validate_players(self, players):
        """Validate that we have players."""
        if not players:
            raise serializers.ValidationError("At least one player required")
        return players


class LineupSubmissionDetailSerializer(serializers.ModelSerializer):
    """Detailed lineup view with club and match info."""

    club_name = serializers.CharField(
        source='club.name',
        read_only=True
    )
    match_str = serializers.CharField(
        source='__str__',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    starters = serializers.SerializerMethodField()
    substitutes = serializers.SerializerMethodField()

    class Meta:
        model = LineupSubmission
        fields = [
            'id', 'match', 'match_str', 'club', 'club_name',
            'formation', 'status', 'status_display',
            'submitted_at', 'confirmed_at', 'locked_at',
            'starters', 'substitutes'
        ]
        read_only_fields = fields

    def get_starters(self, obj):
        """Get starters from the lineup."""
        starters = obj.lineup_entries.filter(
            status=MatchLineup.LineupStatus.STARTER
        ).select_related('player').order_by('formation_position')
        return MatchLineupPlayerSerializer(starters, many=True).data

    def get_substitutes(self, obj):
        """Get substitutes from the lineup."""
        substitutes = obj.lineup_entries.filter(
            status=MatchLineup.LineupStatus.SUBSTITUTE
        ).select_related('player').order_by('shirt_number')
        return MatchLineupPlayerSerializer(substitutes, many=True).data


# ─── Match Report Serializers ──────────────────────────────────────────────


class GoalSerializer(serializers.ModelSerializer):
    """Goal scorer and details."""

    player_name = serializers.CharField(
        source='player.full_name',
        read_only=True
    )
    goal_type_display = serializers.CharField(
        source='get_goal_type_display',
        read_only=True
    )

    class Meta:
        model = Goal
        fields = [
            'id', 'match', 'player', 'player_name', 'club',
            'minute', 'goal_type', 'goal_type_display',
            'assist_player', 'created_at'
        ]
        read_only_fields = [
            'id', 'match', 'created_at'
        ]


class MatchStatsSerializer(serializers.ModelSerializer):
    """Match statistics."""

    possession_display = serializers.SerializerMethodField()

    class Meta:
        model = MatchStats
        fields = [
            'id', 'match', 'club', 'possession', 'possession_display',
            'shots_on_goal', 'shots_off_goal', 'passes', 'passes_accuracy',
            'fouls', 'yellow_cards', 'red_cards', 'corner_kicks',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields

    def get_possession_display(self, obj):
        """Format possession as percentage."""
        return f"{obj.possession}%" if obj.possession else None


class MatchReportSerializer(serializers.ModelSerializer):
    """Match report with goals and statistics."""

    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    goals = GoalSerializer(
        source='goal_set',
        many=True,
        read_only=True
    )
    home_stats = serializers.SerializerMethodField()
    away_stats = serializers.SerializerMethodField()

    class Meta:
        model = MatchReport
        fields = [
            'id', 'match', 'status', 'status_display',
            'home_score', 'away_score', 'home_goals_against',
            'away_goals_against', 'match_duration',
            'goals', 'home_stats', 'away_stats',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields

    def get_home_stats(self, obj):
        """Get home team stats."""
        try:
            stats = obj.match.matchstats_set.get(club=obj.match.home_club)
            return MatchStatsSerializer(stats).data
        except MatchStats.DoesNotExist:
            return None

    def get_away_stats(self, obj):
        """Get away team stats."""
        try:
            stats = obj.match.matchstats_set.get(club=obj.match.away_club)
            return MatchStatsSerializer(stats).data
        except MatchStats.DoesNotExist:
            return None


class MatchReportInputSerializer(serializers.Serializer):
    """Serializer for creating/updating match reports."""

    home_score = serializers.IntegerField(min_value=0)
    away_score = serializers.IntegerField(min_value=0)
    match_duration = serializers.IntegerField(
        min_value=0,
        max_value=180,
        required=False
    )


class GoalInputSerializer(serializers.Serializer):
    """Serializer for recording goals."""

    player_id = serializers.UUIDField()
    club_id = serializers.UUIDField()
    minute = serializers.IntegerField(min_value=1, max_value=180)
    goal_type = serializers.ChoiceField(
        choices=['normal', 'penalty', 'own_goal']
    )
    assist_player_id = serializers.UUIDField(required=False, allow_null=True)
