from django.db import models
from core.models import BaseModel


class JogadorHistoricoClube(BaseModel):
    jogador = models.ForeignKey(
        'accounts.JogadorProfile',
        on_delete=models.CASCADE,
        related_name='clube_history'
    )
    clube = models.ForeignKey(
        'accounts.ClubeProfile',
        on_delete=models.CASCADE,
        related_name='jogador_history'
    )
    data_inicio = models.DateField()
    data_fim = models.DateField(null=True, blank=True)
    numero_camisola = models.IntegerField(null=True, blank=True)
    observacoes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Histórico de Clube de Jogador"
        verbose_name_plural = "Históricos de Clubs de Jogadores"
        ordering = ['-data_inicio']

    def __str__(self):
        return f"{self.jogador.nome_desportivo or self.jogador.nome_completo} - {self.clube.nome} ({self.data_inicio} a {self.data_fim or 'Atual'})"
