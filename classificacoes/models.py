from django.db import models
from core.models import BaseModel, Tenant
from clubs.models import Club
from torneios.models import Tournament, TournamentGroup


class Standing(BaseModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='standings')
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='standings')
    group = models.ForeignKey(TournamentGroup, on_delete=models.CASCADE, related_name='standings', null=True, blank=True)
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='standings')
    played = models.IntegerField(default=0)
    wins = models.IntegerField(default=0)
    draws = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    goals_for = models.IntegerField(default=0)
    goals_against = models.IntegerField(default=0)
    points = models.IntegerField(default=0)

    class Meta:
        unique_together = ('tenant', 'tournament', 'group', 'club')
