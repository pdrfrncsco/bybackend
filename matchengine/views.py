from rest_framework import viewsets, permissions, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from partidas.models import Match
from clubes.models import Club
from jogadores.models import Player
from django.utils import timezone
from drf_spectacular.utils import extend_schema, inline_serializer
from .models import MatchEvent, MatchStats, MatchLineupEntry
from .serializers import (
    MatchEventSerializer,
    MatchStatsSerializer,
    MatchPlayerSerializer,
    LineupToggleSerializer,
    EventCreateSerializer,
    CaptainSetSerializer,
    ManualMatchReportSerializer,
)
from core.permissions import IsManager


MatchEngineStateSerializer = inline_serializer(
    name="MatchEngineState",
    fields={
        "match_status": serializers.CharField(),
        "current_period": serializers.CharField(),
        "timer": serializers.IntegerField(),
        "extra_time": serializers.IntegerField(),
        "events": MatchEventSerializer(many=True),
        "stats": MatchStatsSerializer(),
        "home_lineup": MatchPlayerSerializer(many=True),
        "away_lineup": MatchPlayerSerializer(many=True),
    },
)

MatchEngineLineupSerializer = inline_serializer(
    name="MatchEngineLineup",
    fields={
        "home_lineup": MatchPlayerSerializer(many=True),
        "away_lineup": MatchPlayerSerializer(many=True),
    },
)

MatchEngineControlRequestSerializer = inline_serializer(
    name="MatchEngineControlRequest",
    fields={
        "action": serializers.CharField(),
        "minutes": serializers.IntegerField(required=False),
    },
)

MatchEngineNoopSerializer = inline_serializer(name="MatchEngineNoop", fields={})

class MatchEngineViewSet(viewsets.ViewSet):
    permission_classes = [IsManager]
    serializer_class = MatchEngineNoopSerializer
    queryset = Match.objects.none()

    def _get_match(self, pk, request):
        user = request.user
        queryset = Match.objects.all().select_related('home_team', 'away_team', 'tenant')
        if getattr(user, 'tenant', None):
            queryset = queryset.filter(tenant=user.tenant)
        return get_object_or_404(queryset, pk=pk)

    @action(detail=True, methods=['get'], url_path='state')
    @extend_schema(
        responses=MatchEngineStateSerializer,
        tags=["Match Engine", "Admin/Manager Only"],
        description="Requer role MANAGER ou ADMIN."
    )
    def state(self, request, pk=None):
        match = self._get_match(pk, request)

        stats, _ = MatchStats.objects.get_or_create(
            match=match,
            defaults={
                'tenant': match.tenant,
                'home_possession': 50,
                'away_possession': 50,
                'home_shots': 0,
                'away_shots': 0,
                'home_corners': 0,
                'away_corners': 0,
                'home_fouls': 0,
                'away_fouls': 0,
            },
        )

        events = MatchEvent.objects.filter(match=match).select_related('team', 'player', 'secondary_player').order_by(
            'minute', 'created_at'
        )

        entries = MatchLineupEntry.objects.filter(match=match).select_related('player', 'team')
        home_entries = [e for e in entries if e.team_id == match.home_team_id]
        away_entries = [e for e in entries if e.team_id == match.away_team_id]

        # Calculate current timer
        timer = 0
        if match.status == 'live' and match.period_start_time:
            now = timezone.now()
            elapsed = int((now - match.period_start_time).total_seconds() / 60)
            base_minutes = 0
            if match.current_period == '2H':
                base_minutes = 45
            elif match.current_period == '1ET':
                base_minutes = 90
            elif match.current_period == '2ET':
                base_minutes = 105
            
            timer = base_minutes + elapsed
        elif match.status == 'finished':
            timer = 90 + match.extra_time # Just a fallback

        payload = {
            'match_status': match.status,
            'current_period': match.current_period,
            'timer': timer,
            'extra_time': match.extra_time,
            'events': MatchEventSerializer(events, many=True).data,
            'stats': MatchStatsSerializer(stats).data,
            'home_lineup': self._build_players(home_entries),
            'away_lineup': self._build_players(away_entries),
        }
        return Response(payload)

    @action(detail=True, methods=['post'], url_path='control')
    @extend_schema(
        request=MatchEngineControlRequestSerializer,
        responses=MatchEngineStateSerializer,
        tags=["Match Engine", "Admin/Manager Only"],
        description="Requer role MANAGER ou ADMIN."
    )
    def control(self, request, pk=None):
        match = self._get_match(pk, request)
        action_type = request.data.get('action')
        
        if not action_type:
            return Response({'detail': 'Action required'}, status=status.HTTP_400_BAD_REQUEST)

        now = timezone.now()

        if action_type == 'start_match':
            if match.status == 'scheduled':
                match.status = 'live'
                match.current_period = '1H'
                match.period_start_time = now
                MatchEvent.objects.create(
                    tenant=match.tenant, match=match, team=match.home_team,
                    type='whistle_start', minute=0
                )
        
        elif action_type == 'end_first_half':
            if match.current_period == '1H':
                match.current_period = 'HT'
                match.period_start_time = None
                MatchEvent.objects.create(
                    tenant=match.tenant, match=match, team=match.home_team,
                    type='whistle_end', minute=45 + match.extra_time
                )

        elif action_type == 'start_second_half':
            if match.current_period == 'HT':
                match.current_period = '2H'
                match.period_start_time = now
                match.extra_time = 0 # Reset extra time for new half
                MatchEvent.objects.create(
                    tenant=match.tenant, match=match, team=match.home_team,
                    type='whistle_start', minute=45
                )

        elif action_type == 'end_match':
            if match.status != 'finished':
                match.status = 'finished'
                match.current_period = 'FT'
                match.period_start_time = None
                MatchEvent.objects.create(
                    tenant=match.tenant, match=match, team=match.home_team,
                    type='whistle_end', minute=90 + match.extra_time
                )
                goal_events = MatchEvent.objects.filter(match=match, type='goal')
                home_goals = 0
                away_goals = 0
                for e in goal_events:
                    if not e.is_own_goal:
                        if e.team_id == match.home_team_id:
                            home_goals += 1
                        elif e.team_id == match.away_team_id:
                            away_goals += 1
                    else:
                        if e.team_id == match.home_team_id:
                            away_goals += 1
                        elif e.team_id == match.away_team_id:
                            home_goals += 1
                match.home_score = home_goals
                match.away_score = away_goals
                
                # Update stats
                from .services import MatchStatsService
                MatchStatsService.process_match_completion(match)

        elif action_type == 'add_time':
            minutes = int(request.data.get('minutes', 0))
            match.extra_time = minutes

        match.save()
        
        # Return updated state
        return self.state(request, pk=pk)

    @action(detail=True, methods=['post'], url_path='events')
    @extend_schema(
        request=EventCreateSerializer,
        responses=MatchEventSerializer,
        tags=["Match Engine", "Admin/Manager Only"],
        description="Requer role MANAGER ou ADMIN."
    )
    def create_event(self, request, pk=None):
        match = self._get_match(pk, request)
        serializer = EventCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        team = get_object_or_404(Club, pk=data['team_id'])
        player = None
        secondary_player = None
        if data.get('player_id'):
            player = get_object_or_404(Player, pk=data['player_id'])
        if data.get('secondary_player_id'):
            secondary_player = get_object_or_404(Player, pk=data['secondary_player_id'])

        event = MatchEvent.objects.create(
            tenant=match.tenant,
            match=match,
            team=team,
            player=player,
            secondary_player=secondary_player,
            type=data['type'],
            minute=data['minute'],
            is_own_goal=data.get('is_own_goal', False),
        )

        return Response(MatchEventSerializer(event).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='stats')
    @extend_schema(
        request=MatchStatsSerializer,
        responses=MatchStatsSerializer,
        tags=["Match Engine", "Admin/Manager Only"],
        description="Requer role MANAGER ou ADMIN."
    )
    def update_stats(self, request, pk=None):
        match = self._get_match(pk, request)
        stats, _ = MatchStats.objects.get_or_create(match=match, defaults={'tenant': match.tenant})
        serializer = MatchStatsSerializer(stats, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='toggle_lineup')
    @extend_schema(
        request=LineupToggleSerializer,
        responses=MatchEngineLineupSerializer,
        tags=["Match Engine", "Admin/Manager Only"],
        description="Requer role MANAGER ou ADMIN."
    )
    def toggle_lineup(self, request, pk=None):
        match = self._get_match(pk, request)
        serializer = LineupToggleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        team = get_object_or_404(Club, pk=data['team_id'])
        player = get_object_or_404(Player, pk=data['player_id'])

        entry, _ = MatchLineupEntry.objects.get_or_create(
            tenant=match.tenant,
            match=match,
            team=team,
            player=player,
            defaults={
                'number': player.number,
                'position': player.position,
                'is_starter': True,
                'is_captain': player.is_captain,
            },
        )

        entry.is_starter = not entry.is_starter
        entry.save()

        entries = MatchLineupEntry.objects.filter(match=match).select_related('player', 'team')
        home_entries = [e for e in entries if e.team_id == match.home_team_id]
        away_entries = [e for e in entries if e.team_id == match.away_team_id]

        payload = {
            'home_lineup': self._build_players(home_entries),
            'away_lineup': self._build_players(away_entries),
        }
        return Response(payload)

    def _build_players(self, entry_list):
        data = []
        for e in entry_list:
            p = e.player
            if not p:
                continue
            data.append(
                {
                    'id': p.id,
                    'name': p.name,
                    'number': e.number if e.number is not None else p.number,
                    'position': e.position or p.position,
                    'is_starter': e.is_starter,
                    'is_captain': e.is_captain,
                }
            )
        serializer = MatchPlayerSerializer(data, many=True)
        return serializer.data

    @action(detail=True, methods=['post'], url_path='set_captain')
    @extend_schema(
        request=CaptainSetSerializer,
        responses=MatchEngineLineupSerializer,
        tags=["Match Engine", "Admin/Manager Only"],
        description="Requer role MANAGER ou ADMIN."
    )
    def set_captain(self, request, pk=None):
        match = self._get_match(pk, request)
        serializer = CaptainSetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        team = get_object_or_404(Club, pk=data['team_id'])
        if team.id not in (match.home_team_id, match.away_team_id):
            return Response({'detail': 'Equipa não pertence a este jogo.'}, status=status.HTTP_400_BAD_REQUEST)

        player = get_object_or_404(Player, pk=data['player_id'])

        entry, _ = MatchLineupEntry.objects.get_or_create(
            tenant=match.tenant,
            match=match,
            team=team,
            player=player,
            defaults={
                'number': player.number,
                'position': player.position,
                'is_starter': True,
                'is_captain': False,
            },
        )

        if entry.is_captain:
            entry.is_captain = False
            entry.save()
        else:
            MatchLineupEntry.objects.filter(match=match, team=team).exclude(pk=entry.pk).update(is_captain=False)
            entry.is_captain = True
            entry.save()

        entries = MatchLineupEntry.objects.filter(match=match).select_related('player', 'team')
        home_entries = [e for e in entries if e.team_id == match.home_team_id]
        away_entries = [e for e in entries if e.team_id == match.away_team_id]

        payload = {
            'home_lineup': self._build_players(home_entries),
            'away_lineup': self._build_players(away_entries),
        }
        return Response(payload)

    @action(detail=True, methods=['post'], url_path='manual_report')
    @extend_schema(
        request=ManualMatchReportSerializer,
        responses=MatchEngineStateSerializer,
        tags=["Match Engine", "Admin/Manager Only"],
        description="Permite o preenchimento manual de toda a ficha de jogo."
    )
    def manual_report(self, request, pk=None):
        from django.db import transaction
        from .services import MatchStatsService

        match = self._get_match(pk, request)
        serializer = ManualMatchReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        with transaction.atomic():
            # 1. Clear existing data
            MatchEvent.objects.filter(match=match).delete()
            MatchLineupEntry.objects.filter(match=match).delete()
            MatchStats.objects.filter(match=match).delete()

            # 2. Update Match basic info
            match.home_score = data['home_score']
            match.away_score = data['away_score']
            match.status = 'finished'
            match.current_period = 'FT'
            match.save()

            # 3. Create Lineups
            for entry_data in data['home_lineup'] + data['away_lineup']:
                player = get_object_or_404(Player, pk=entry_data['player_id'])
                team = get_object_or_404(Club, pk=entry_data['team_id'])
                MatchLineupEntry.objects.create(
                    tenant=match.tenant,
                    match=match,
                    team=team,
                    player=player,
                    number=entry_data.get('number', player.number),
                    position=entry_data.get('position', player.position),
                    is_starter=entry_data['is_starter'],
                    is_captain=entry_data.get('is_captain', False)
                )

            # 4. Create Events
            for event_data in data.get('events', []):
                team = get_object_or_404(Club, pk=event_data['team_id'])
                player = None
                secondary_player = None
                if event_data.get('player_id'):
                    player = get_object_or_404(Player, pk=event_data['player_id'])
                if event_data.get('secondary_player_id'):
                    secondary_player = get_object_or_404(Player, pk=event_data['secondary_player_id'])
                
                MatchEvent.objects.create(
                    tenant=match.tenant,
                    match=match,
                    team=team,
                    player=player,
                    secondary_player=secondary_player,
                    type=event_data['type'],
                    minute=event_data['minute'],
                    is_own_goal=event_data.get('is_own_goal', False)
                )

            # 5. Create/Update Stats
            stats_data = data.get('stats', {})
            MatchStats.objects.create(
                tenant=match.tenant,
                match=match,
                home_possession=stats_data.get('home_possession', 50),
                away_possession=stats_data.get('away_possession', 50),
                home_shots=stats_data.get('home_shots', 0),
                away_shots=stats_data.get('away_shots', 0),
                home_corners=stats_data.get('home_corners', 0),
                away_corners=stats_data.get('away_corners', 0),
                home_fouls=stats_data.get('home_fouls', 0),
                away_fouls=stats_data.get('away_fouls', 0),
            )

            # 6. Trigger historical updates
            MatchStatsService.process_match_completion(match)

        return self.state(request, pk=pk)
