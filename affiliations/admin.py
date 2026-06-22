from django.contrib import admin
from affiliations.models import (
    ClubeOrganizacaoRequest,
    JogadorClubeRequest,
    JogadorHistoricoClube,
)


@admin.register(ClubeOrganizacaoRequest)
class ClubeOrganizacaoRequestAdmin(admin.ModelAdmin):
    list_display = ('clube', 'organizacao', 'estado', 'data_pedido', 'data_decisao')
    search_fields = ('clube__nome', 'organizacao__nome', 'mensagem')
    list_filter = ('estado', 'data_pedido', 'data_decisao')


@admin.register(JogadorClubeRequest)
class JogadorClubeRequestAdmin(admin.ModelAdmin):
    list_display = ('jogador', 'clube', 'estado', 'data_pedido', 'data_decisao')
    search_fields = ('jogador__nome_completo', 'jogador__nome_desportivo', 'clube__nome', 'mensagem')
    list_filter = ('estado', 'data_pedido', 'data_decisao')


@admin.register(JogadorHistoricoClube)
class JogadorHistoricoClubeAdmin(admin.ModelAdmin):
    list_display = ('jogador', 'clube', 'data_inicio', 'data_fim', 'numero_camisola')
    search_fields = ('jogador__nome_completo', 'jogador__nome_desportivo', 'clube__nome')
    list_filter = ('data_inicio', 'data_fim')
