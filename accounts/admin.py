from django.contrib import admin
from accounts.models import (
    OrganizacaoProfile,
    ClubeProfile,
    JogadorProfile,
    AdeptoProfile,
)


@admin.register(OrganizacaoProfile)
class OrganizacaoProfileAdmin(admin.ModelAdmin):
    list_display = ('nome', 'sigla', 'email', 'telefone', 'pais', 'status', 'created_at')
    search_fields = ('nome', 'sigla', 'email', 'user__username', 'user__email')
    list_filter = ('status', 'pais', 'created_at')
    raw_id_fields = ('user',)


@admin.register(ClubeProfile)
class ClubeProfileAdmin(admin.ModelAdmin):
    list_display = ('nome', 'sigla', 'email', 'telefone', 'estadio', 'created_at')
    search_fields = ('nome', 'sigla', 'email', 'estadio', 'user__username', 'user__email')
    list_filter = ('fundacao', 'created_at')
    raw_id_fields = ('user',)


@admin.register(JogadorProfile)
class JogadorProfileAdmin(admin.ModelAdmin):
    list_display = ('nome_completo', 'nome_desportivo', 'nacionalidade', 'posicao', 'agente', 'created_at')
    search_fields = ('nome_completo', 'nome_desportivo', 'nacionalidade', 'posicao', 'agente', 'user__username', 'user__email')
    list_filter = ('pe_preferencial', 'posicao', 'created_at')
    raw_id_fields = ('user',)


@admin.register(AdeptoProfile)
class AdeptoProfileAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cidade', 'pais', 'created_at')
    search_fields = ('nome', 'cidade', 'pais', 'user__username', 'user__email')
    list_filter = ('cidade', 'pais', 'created_at')
    raw_id_fields = ('user',)
    filter_horizontal = ('clubs_favoritos', 'jogadores_favoritos')
