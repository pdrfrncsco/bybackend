from django.db import models
from core.models import BaseModel, Tenant
from clubs.models import Club
from estadios.models import Stadium
from torneios.models import Tournament
from arbitros.models import Referee

class Match(BaseModel):
    STATUS_CHOICES = [
        ('scheduled', 'Agendado'),
        ('live', 'Ao Vivo'),
        ('finished', 'Terminado'),
        ('postponed', 'Adiado'),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='matches')
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='matches', null=True, blank=True)
    home_team = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='home_matches')
    away_team = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='away_matches')
    home_score = models.IntegerField(null=True, blank=True)
    away_score = models.IntegerField(null=True, blank=True)
    date = models.DateTimeField()
    venue = models.ForeignKey(Stadium, on_delete=models.SET_NULL, null=True, blank=True, related_name='matches')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    round = models.CharField(max_length=100, blank=True)
    referee = models.ForeignKey(Referee, on_delete=models.SET_NULL, null=True, blank=True, related_name='matches')
    assistant_referees = models.ManyToManyField(Referee, related_name='assistant_matches', blank=True)
    home_coach = models.ForeignKey('treinadores.Treinador', on_delete=models.SET_NULL, null=True, blank=True, related_name='home_matches')
    away_coach = models.ForeignKey('treinadores.Treinador', on_delete=models.SET_NULL, null=True, blank=True, related_name='away_matches')
    
    # Game State / Timing
    current_period = models.CharField(max_length=10, blank=True, default='', choices=[
        ('1H', '1ª Parte'),
        ('HT', 'Intervalo'),
        ('2H', '2ª Parte'),
        ('FT', 'Terminado'),
    ])
    period_start_time = models.DateTimeField(null=True, blank=True)
    extra_time = models.IntegerField(default=0) # Minutes of added time
    stats_processed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.home_team} vs {self.away_team}"
