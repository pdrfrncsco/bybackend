from django.db import models
from core.models import BaseModel, Tenant
from clubes.models import Club

class Tournament(BaseModel):
    STATUS_CHOICES = [
        ('active', 'Em andamento'),
        ('upcoming', 'Inscrições'),
        ('completed', 'Terminado'),
    ]
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='tournaments')
    name = models.CharField(max_length=255)
    season = models.CharField(max_length=50) # e.g. 2024/2025
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    logo = models.ImageField(upload_to='tournaments/', null=True, blank=True)
    is_public = models.BooleanField(default=False)
    
    # Configuration
    max_teams = models.IntegerField(default=16)
    type = models.CharField(max_length=50, default='League', choices=[
        ('League', 'Liga (Pontos corridos)'),
        ('Knockout', 'Mata-Mata'),
        ('Groups', 'Fase de Grupos + Eliminatória')
    ])
    
    clubs = models.ManyToManyField(Club, related_name='tournaments', blank=True)
    champion_club = models.ForeignKey(
        Club,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tournaments_won',
    )
    runner_up_club = models.ForeignKey(
        Club,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tournaments_runner_up',
    )

    def __str__(self):
        return f"{self.name} ({self.season})"

    @property
    def progress(self) -> int:
        from partidas.models import Match

        total_matches = Match.objects.filter(tournament=self).count()
        if total_matches == 0:
            if self.status == 'completed':
                return 100
            return 0

        played_matches = Match.objects.filter(tournament=self, status='finished').count()
        progress = int(round((played_matches / total_matches) * 100))

        if self.status == 'completed':
            return 100

        if progress < 0:
            progress = 0
        if progress > 100:
            progress = 100
        return progress

class TournamentGroup(BaseModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='tournament_groups')
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='groups')
    name = models.CharField(max_length=50) # Group A, Group B
    clubs = models.ManyToManyField(Club, related_name='tournament_groups', blank=True)

    def __str__(self):
        return f"{self.name} - {self.tournament.name}"

