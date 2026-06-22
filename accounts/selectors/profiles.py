from django.db.models import QuerySet
from accounts.models import (
    OrganizacaoProfile,
    ClubeProfile,
    JogadorProfile,
    AdeptoProfile,
)


def get_organizacao_profiles() -> QuerySet[OrganizacaoProfile]:
    """
    Retorna todos os perfis de organizações com carregamento otimizado do user.
    """
    return OrganizacaoProfile.objects.select_related('user').all()


def get_clube_profiles() -> QuerySet[ClubeProfile]:
    """
    Retorna todos os perfis de clubes com carregamento otimizado do user.
    """
    return ClubeProfile.objects.select_related('user').all()


def get_jogador_profiles() -> QuerySet[JogadorProfile]:
    """
    Retorna todos os perfis de jogadores com carregamento otimizado do user.
    """
    return JogadorProfile.objects.select_related('user').all()


def get_adepto_profiles() -> QuerySet[AdeptoProfile]:
    """
    Retorna todos os perfis de adeptos com carregamento otimizado de user, clubes e jogadores favoritos.
    """
    return AdeptoProfile.objects.select_related('user').prefetch_related(
        'clubes_favoritos',
        'jogadores_favoritos'
    ).all()
