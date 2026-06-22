from django.db import models
from django.db.models import Q
from core.models import BaseModel, Tenant
from clubes.models import Club


class Treinador(BaseModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='treinadores')

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    nacionalidade = models.CharField(max_length=100)
    data_nascimento = models.DateField()
    foto = models.ImageField(upload_to='treinadores/', null=True, blank=True)
    estilo_jogo = models.TextField()
    biografia = models.TextField()

    class Meta:
        ordering = ['last_name', 'first_name', 'id']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class HistoricoTreinador(BaseModel):
    CARGO_CHOICES = (
        ('Treinador Principal', 'Treinador Principal'),
        ('Treinador Adjunto', 'Treinador Adjunto'),
        ('Treinador Interino', 'Treinador Interino'),
        ('Preparador Físico', 'Preparador Físico'),
        ('Treinador de Guarda-Redes', 'Treinador de Guarda-Redes'),
        ('Analista', 'Analista'),
        ('Outro', 'Outro'),
    )

    treinador = models.ForeignKey(Treinador, on_delete=models.CASCADE, related_name='historico')
    clube = models.ForeignKey(Club, on_delete=models.PROTECT, related_name='historico_treinadores')
    cargo = models.CharField(max_length=50, choices=CARGO_CHOICES, default='Treinador Principal')
    data_inicio = models.DateField(db_index=True)
    data_fim = models.DateField(null=True, blank=True, db_index=True)

    jogos = models.PositiveIntegerField(default=0)
    vitorias = models.PositiveIntegerField(default=0)
    empates = models.PositiveIntegerField(default=0)
    derrotas = models.PositiveIntegerField(default=0)
    conquistas = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-data_inicio', '-created_at', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['treinador'],
                condition=Q(data_fim__isnull=True),
                name='unique_current_club_per_treinador',
            ),
        ]

    def __str__(self):
        return f"{self.treinador} - {self.clube} ({self.cargo})"


class LicencaTreinador(BaseModel):
    treinador = models.ForeignKey(Treinador, on_delete=models.CASCADE, related_name='licencas')
    nome = models.CharField(max_length=255)
    entidade = models.CharField(max_length=100)
    data_emissao = models.DateField()
    data_validade = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-data_emissao', 'id']

    def __str__(self):
        return f"{self.nome} ({self.entidade}) - {self.treinador}"

