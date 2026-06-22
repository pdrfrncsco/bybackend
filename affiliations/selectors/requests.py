from django.db.models import QuerySet
from affiliations.models import ClubeOrganizacaoRequest, JogadorClubeRequest, JogadorHistoricoClube


def get_clube_organizacao_requests() -> QuerySet[ClubeOrganizacaoRequest]:
    """
    Retorna todos os pedidos de afiliação de clube a organização de forma otimizada.
    """
    return ClubeOrganizacaoRequest.objects.select_related(
        'clube',
        'clube__user',
        'organizacao',
        'organizacao__user'
    ).all()


def get_jogador_clube_requests() -> QuerySet[JogadorClubeRequest]:
    """
    Retorna todos os pedidos de ingresso de jogador a clube de forma otimizada.
    """
    return JogadorClubeRequest.objects.select_related(
        'jogador',
        'jogador__user',
        'clube',
        'clube__user'
    ).all()


def get_jogador_historico_clubes() -> QuerySet[JogadorHistoricoClube]:
    """
    Retorna todos os históricos de clubes de jogadores de forma otimizada.
    """
    return JogadorHistoricoClube.objects.select_related(
        'jogador',
        'jogador__user',
        'clube',
        'clube__user'
    ).all()
