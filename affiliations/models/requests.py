from django.db import models
from core.models import BaseModel
from .request_status import RequestStatus


class ClubeOrganizacaoRequest(BaseModel):
    clube = models.ForeignKey(
        'accounts.ClubeProfile',
        on_delete=models.CASCADE,
        related_name='organizacao_requests'
    )
    organizacao = models.ForeignKey(
        'accounts.OrganizacaoProfile',
        on_delete=models.CASCADE,
        related_name='clube_requests'
    )
    estado = models.CharField(
        max_length=20,
        choices=RequestStatus.choices,
        default=RequestStatus.PENDING
    )
    mensagem = models.TextField(blank=True)
    data_pedido = models.DateTimeField(auto_now_add=True)
    data_decisao = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Pedido de Afiliação Clube-Organização"
        verbose_name_plural = "Pedidos de Afiliação Clube-Organização"
        ordering = ['-data_pedido']

    def __str__(self):
        return f"{self.clube.nome} -> {self.organizacao.nome} ({self.estado})"


class JogadorClubeRequest(BaseModel):
    jogador = models.ForeignKey(
        'accounts.JogadorProfile',
        on_delete=models.CASCADE,
        related_name='clube_requests'
    )
    clube = models.ForeignKey(
        'accounts.ClubeProfile',
        on_delete=models.CASCADE,
        related_name='jogador_requests'
    )
    estado = models.CharField(
        max_length=20,
        choices=RequestStatus.choices,
        default=RequestStatus.PENDING
    )
    mensagem = models.TextField(blank=True)
    data_pedido = models.DateTimeField(auto_now_add=True)
    data_decisao = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Pedido de Ingresso Jogador-Clube"
        verbose_name_plural = "Pedidos de Ingresso Jogador-Clube"
        ordering = ['-data_pedido']

    def __str__(self):
        return f"{self.jogador.nome_desportivo or self.jogador.nome_completo} -> {self.clube.nome} ({self.estado})"
