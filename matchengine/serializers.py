from rest_framework import serializers
from .models import MatchEvent, MatchStats, MatchLineupEntry
from jogadores.models import Player


class MatchEventSerializer(serializers.ModelSerializer):
    team_id = serializers.UUIDField(source='team.id', read_only=True)
    player_id = serializers.UUIDField(source='player.id', read_only=True)
    secondary_player_id = serializers.UUIDField(source='secondary_player.id', read_only=True)
    player_name = serializers.CharField(source='player.name', read_only=True)
    secondary_player_name = serializers.CharField(source='secondary_player.name', read_only=True)

    class Meta:
        model = MatchEvent
        fields = [
            'id',
            'match',
            'team_id',
            'player_id',
            'secondary_player_id',
            'type',
            'minute',
            'is_own_goal',
            'player_name',
            'secondary_player_name',
        ]
        read_only_fields = ['id', 'match']


class MatchStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MatchStats
        fields = [
            'home_possession',
            'away_possession',
            'home_shots',
            'away_shots',
            'home_corners',
            'away_corners',
            'home_fouls',
            'away_fouls',
        ]


class MatchPlayerSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    number = serializers.IntegerField(allow_null=True)
    position = serializers.CharField()
    is_starter = serializers.BooleanField()
    is_captain = serializers.BooleanField()


class LineupToggleSerializer(serializers.Serializer):
    team_id = serializers.UUIDField()
    player_id = serializers.UUIDField()


class CaptainSetSerializer(serializers.Serializer):
    team_id = serializers.UUIDField()
    player_id = serializers.UUIDField()


class EventCreateSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=[c[0] for c in MatchEvent.EVENT_TYPES])
    minute = serializers.IntegerField(min_value=0)
    team_id = serializers.UUIDField()
    player_id = serializers.UUIDField(required=False, allow_null=True)
    secondary_player_id = serializers.UUIDField(required=False, allow_null=True)
    is_own_goal = serializers.BooleanField(required=False)

class ManualMatchReportLineupSerializer(serializers.Serializer):
    player_id = serializers.UUIDField()
    team_id = serializers.UUIDField()
    number = serializers.IntegerField(required=False, allow_null=True)
    position = serializers.CharField(required=False, allow_blank=True)
    is_starter = serializers.BooleanField(default=True)
    is_captain = serializers.BooleanField(default=False)

class ManualMatchReportSerializer(serializers.Serializer):
    home_score = serializers.IntegerField(min_value=0)
    away_score = serializers.IntegerField(min_value=0)
    home_lineup = ManualMatchReportLineupSerializer(many=True)
    away_lineup = ManualMatchReportLineupSerializer(many=True)
    events = EventCreateSerializer(many=True, required=False)
    stats = MatchStatsSerializer(required=False)
