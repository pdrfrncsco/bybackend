from django.contrib import admin
from .models import Treinador, HistoricoTreinador, LicencaTreinador


class HistoricoTreinadorInline(admin.TabularInline):
    model = HistoricoTreinador
    extra = 0
    fields = (
        'clube',
        'cargo',
        'data_inicio',
        'data_fim',
        'jogos',
        'vitorias',
        'empates',
        'derrotas',
    )


class LicencaTreinadorInline(admin.TabularInline):
    model = LicencaTreinador
    extra = 0
    fields = ('nome', 'entidade', 'data_emissao', 'data_validade')


@admin.register(Treinador)
class TreinadorAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'nacionalidade', 'data_nascimento', 'tenant')
    list_filter = ('tenant', 'nacionalidade')
    search_fields = ('first_name', 'last_name')
    inlines = [HistoricoTreinadorInline, LicencaTreinadorInline]


@admin.register(HistoricoTreinador)
class HistoricoTreinadorAdmin(admin.ModelAdmin):
    list_display = ('treinador', 'clube', 'cargo', 'data_inicio', 'data_fim')
    list_filter = ('cargo', 'clube')
    search_fields = ('treinador__first_name', 'treinador__last_name', 'clube__name')


@admin.register(LicencaTreinador)
class LicencaTreinadorAdmin(admin.ModelAdmin):
    list_display = ('treinador', 'nome', 'entidade', 'data_emissao', 'data_validade')
    list_filter = ('entidade',)
    search_fields = ('treinador__first_name', 'treinador__last_name', 'nome', 'entidade')

