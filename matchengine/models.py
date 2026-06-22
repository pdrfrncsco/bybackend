from django.db import models
from core.models import BaseModel, Tenant
from partidas.models import Match
from clubes.models import Club
from jogadores.models import Player


class MatchEvent(BaseModel):
    EVENT_TYPES = [
        ('goal', 'Golo'),
        ('yellow_card', 'Cartão Amarelo'),
        ('red_card', 'Cartão Vermelho'),
        ('substitution', 'Substituição'),
        ('whistle_start', 'Início de jogo'),
        ('whistle_end', 'Fim de jogo'),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='match_events')
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='events')
    team = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='match_events')
    player = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, related_name='match_events')
    secondary_player = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, related_name='secondary_match_events')
    type = models.CharField(max_length=32, choices=EVENT_TYPES)
    minute = models.IntegerField(default=0)
    is_own_goal = models.BooleanField(default=False)

    class Meta:
        ordering = ['minute', 'created_at']


class MatchStats(BaseModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='match_stats')
    match = models.OneToOneField(Match, on_delete=models.CASCADE, related_name='stats')

    home_possession = models.IntegerField(default=50)
    away_possession = models.IntegerField(default=50)
    home_shots = models.IntegerField(default=0)
    away_shots = models.IntegerField(default=0)
    home_corners = models.IntegerField(default=0)
    away_corners = models.IntegerField(default=0)
    home_fouls = models.IntegerField(default=0)
    away_fouls = models.IntegerField(default=0)


class MatchLineupEntry(BaseModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='match_lineups')
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='lineup_entries')
    team = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='lineup_entries')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='lineup_entries')

    number = models.IntegerField(null=True, blank=True)
    position = models.CharField(max_length=50, blank=True)
    is_starter = models.BooleanField(default=True)
    is_captain = models.BooleanField(default=False)

    class Meta:
        unique_together = ('match', 'team', 'player')

