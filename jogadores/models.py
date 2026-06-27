from django.db import models
from django.db.models import Q
from core.models import BaseModel, Tenant
from clubs.models import Club

class Player(BaseModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='players')
    name = models.CharField(max_length=255)
    nickname = models.CharField(max_length=100, blank=True)
    shirt_name = models.CharField(max_length=15, blank=True)
    position = models.CharField(max_length=50, default='Avançado', choices=[
        ('Avançado', 'Avançado'),
        ('Extremo-direito', 'Extremo Direito'),
        ('Extremo-esquerdo', 'Extremo Esquerdo'),
        ('Meio-campo', 'Meio-campo'),
        ('Médio-direito', 'Médio Direito'),
        ('Médio-esquerdo', 'Médio Esquerdo'),
        ('Defesa-central', 'Defesa Central'),
        ('Lateral-esquerdo', 'Lateral Esquerdo'),
        ('Lateral-direito', 'Lateral Direito'),
        ('Guarda-Redes', 'Guarda Redes')


    ])
    number = models.IntegerField(null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    nationality = models.CharField(max_length=100, default='Angolana')
    avatar = models.ImageField(upload_to='players/', null=True, blank=True)
    is_captain = models.BooleanField(default=False)
    is_starter = models.BooleanField(default=False)

    club = models.ForeignKey(Club, on_delete=models.SET_NULL, null=True, blank=True, related_name='players')
    last_club = models.ForeignKey(Club, on_delete=models.SET_NULL, null=True, blank=True, related_name='last_players')

    # Detailed Info
    date_of_birth = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, default='active', choices=[
        ('active', 'Activo'),
        ('injured', 'Lesionado'),
        ('suspended', 'Suspenso')
    ])
    height = models.IntegerField(null=True, blank=True, help_text="cm")
    weight = models.IntegerField(null=True, blank=True, help_text="kg")
    foot = models.CharField(max_length=20, default='Direito', choices=[
        ('Direito', 'Direito'),
        ('Esquerdo', 'Esquerdo'),
        ('Ambidestro', 'Ambidestro')
    ])
    joined_date = models.DateField(null=True, blank=True)
    clube_profile = models.ForeignKey(
        'accounts.ClubeProfile',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='associated_players'
    )
    jogador_profile = models.OneToOneField(
        'accounts.JogadorProfile',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='athlete'
    )

    def __str__(self):
        return self.name

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['club', 'number'],
                condition=Q(number__isnull=False),
                name='unique_player_number_per_club',
            ),
        ]

class PlayerHistory(BaseModel):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='history')
    season = models.CharField(max_length=50)
    placement = models.CharField(max_length=50, blank=True)
    is_trophy = models.BooleanField(default=False)
    club = models.ForeignKey(Club, on_delete=models.SET_NULL, null=True, blank=True, related_name='player_history')
    matches = models.IntegerField(default=0)
    goals = models.IntegerField(default=0)
    assists = models.IntegerField(default=0)
    minutes = models.IntegerField(default=0)
    yellow_cards = models.IntegerField(default=0)
    red_cards = models.IntegerField(default=0)

    class Meta:
        ordering = ['-season']
