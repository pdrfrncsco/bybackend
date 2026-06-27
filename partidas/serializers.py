from rest_framework import serializers
from django.utils import timezone
from django.db.models import Q
from .models import Match
from clubs.serializers import ClubBasicSerializer
from estadios.serializers import StadiumSerializer
from treinadores.models import HistoricoTreinador

class MatchSerializer(serializers.ModelSerializer):
    home_team_name = serializers.SerializerMethodField()
    away_team_name = serializers.SerializerMethodField()
    home_team_logo = serializers.SerializerMethodField()
    home_team_logo = serializers.SerializerMethodField()
    away_team_logo = serializers.SerializerMethodField()
    home_team_details = ClubBasicSerializer(source='home_team', read_only=True)
    away_team_details = ClubBasicSerializer(source='away_team', read_only=True)
    venue_details = StadiumSerializer(source='venue', read_only=True)
    live_minute = serializers.SerializerMethodField()
    home_coach_name = serializers.SerializerMethodField()
    away_coach_name = serializers.SerializerMethodField()

    class Meta:
        model = Match
        fields = [
            'id',
            'tournament',
            'home_team',
            'away_team',
            'home_team_name',
            'away_team_name',
            'home_team_logo',
            'away_team_logo',
            'home_team_details',
            'away_team_details',
            'home_score',
            'away_score',
            'date',
            'venue',
            'venue_details',
            'status',
            'round',
            'referee',
            'assistant_referees',
            'home_coach',
            'away_coach',
            'home_coach_name',
            'away_coach_name',
            'current_period',
            'extra_time',
            'live_minute',
        ]

    def get_home_team_name(self, obj) -> str:
        return obj.home_team.name if obj.home_team else "TBD"

    def get_away_team_name(self, obj) -> str:
        return obj.away_team.name if obj.away_team else "TBD"

    def get_home_team_logo(self, obj) -> str | None:
        request = self.context.get('request')
        if obj.home_team and obj.home_team.logo:
            url = obj.home_team.logo.url
            return request.build_absolute_uri(url) if request else url
        return None

    def get_away_team_logo(self, obj) -> str | None:
        request = self.context.get('request')
        if obj.away_team and obj.away_team.logo:
            url = obj.away_team.logo.url
            return request.build_absolute_uri(url) if request else url
        return None

    def get_live_minute(self, obj):
        if obj.status != 'live' or not obj.period_start_time:
            return None
        now = timezone.now()
        delta = now - obj.period_start_time
        minutes = int(delta.total_seconds() // 60)
        base = 0
        if obj.current_period == '2H':
            base = 45
        if minutes < 0:
            minutes = 0
        return base + minutes

    def _coach_name_if_valid(self, coach, club, date) -> str | None:
        if not coach or not club or not date:
            return None
        target_date = date.date()
        exists = HistoricoTreinador.objects.filter(
            treinador=coach,
            clube=club,
            data_inicio__lte=target_date,
        ).filter(
            Q(data_fim__isnull=True) | Q(data_fim__gte=target_date),
        ).exists()
        if not exists:
            return None
        first = getattr(coach, 'first_name', '') or ''
        last = getattr(coach, 'last_name', '') or ''
        full = f'{first} {last}'.strip()
        return full or str(coach)

    def get_home_coach_name(self, obj) -> str | None:
        return self._coach_name_if_valid(obj.home_coach, obj.home_team, obj.date)

    def get_away_coach_name(self, obj) -> str | None:
        return self._coach_name_if_valid(obj.away_coach, obj.away_team, obj.date)
