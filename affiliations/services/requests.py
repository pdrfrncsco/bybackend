from datetime import date
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from affiliations.models import ClubeOrganizacaoRequest, JogadorClubeRequest, JogadorHistoricoClube, RequestStatus
from accounts.models import UserRole


@transaction.atomic
def create_clube_organizacao_request(clube_profile, organizacao_profile, mensagem="") -> ClubeOrganizacaoRequest:
    """
    Cria um pedido de afiliação de um clube para uma organização.
    Garante que não há outro pedido pendente igual.
    """
    existing_pending = ClubeOrganizacaoRequest.objects.filter(
        clube=clube_profile,
        organizacao=organizacao_profile,
        estado=RequestStatus.PENDING
    ).exists()
    
    if existing_pending:
        raise ValueError("Já existe um pedido de afiliação pendente para esta organização.")

    return ClubeOrganizacaoRequest.objects.create(
        clube=clube_profile,
        organizacao=organizacao_profile,
        mensagem=mensagem
    )


@transaction.atomic
def decide_clube_organizacao_request(request_id, status, user_decisor, mensagem_resposta=None) -> ClubeOrganizacaoRequest:
    """
    Aprova ou rejeita um pedido de afiliação clube-organização.
    Se aprovado, atualiza o modelo Club associado.
    """
    try:
        req = ClubeOrganizacaoRequest.objects.select_related('clube', 'organizacao').get(pk=request_id)
    except ClubeOrganizacaoRequest.DoesNotExist:
        raise ValueError("Pedido não encontrado.")

    if req.estado != RequestStatus.PENDING:
        raise ValueError("Este pedido já foi decidido.")

    # Validar que quem decide é o proprietário da organização ou um admin
    is_admin = user_decisor.role in [UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.LEGACY_ADMIN] or user_decisor.is_superuser
    is_org_owner = req.organizacao.user == user_decisor

    if not (is_admin or is_org_owner):
        raise PermissionDenied("Não tem permissão para decidir sobre este pedido.")

    req.estado = status
    req.data_decisao = timezone.now()
    if mensagem_resposta:
        req.mensagem += f"\n[Resposta]: {mensagem_resposta}"
    req.save()

    if status == RequestStatus.APPROVED:
        # Se o perfil do clube estiver associado a um modelo Club de negócio, vincula-os
        club = getattr(req.clube, 'business_club', None)
        if club:
            club.organizacao = req.organizacao
            club.save(update_fields=['organizacao'])

    return req


@transaction.atomic
def create_jogador_clube_request(jogador_profile, clube_profile, mensagem="") -> JogadorClubeRequest:
    """
    Cria um pedido de ingresso de um jogador para um clube.
    """
    existing_pending = JogadorClubeRequest.objects.filter(
        jogador=jogador_profile,
        clube=clube_profile,
        estado=RequestStatus.PENDING
    ).exists()
    
    if existing_pending:
        raise ValueError("Já existe um pedido de ingresso pendente para este clube.")

    return JogadorClubeRequest.objects.create(
        jogador=jogador_profile,
        clube=clube_profile,
        mensagem=mensagem
    )


@transaction.atomic
def decide_jogador_clube_request(request_id, status, user_decisor, mensagem_resposta=None) -> JogadorClubeRequest:
    """
    Aprova ou rejeita um pedido de ingresso jogador-clube.
    Se aprovado, atualiza o modelo Player e inicia o histórico de clubes.
    """
    try:
        req = JogadorClubeRequest.objects.select_related('jogador', 'clube').get(pk=request_id)
    except JogadorClubeRequest.DoesNotExist:
        raise ValueError("Pedido não encontrado.")

    if req.estado != RequestStatus.PENDING:
        raise ValueError("Este pedido já foi decidido.")

    # Validar que quem decide é o dono do clube ou um admin
    is_admin = user_decisor.role in [UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.LEGACY_ADMIN] or user_decisor.is_superuser
    is_club_owner = req.clube.user == user_decisor

    if not (is_admin or is_club_owner):
        raise PermissionDenied("Não tem permissão para decidir sobre este pedido.")

    req.estado = status
    req.data_decisao = timezone.now()
    if mensagem_resposta:
        req.mensagem += f"\n[Resposta]: {mensagem_resposta}"
    req.save()

    if status == RequestStatus.APPROVED:
        player = getattr(req.jogador, 'athlete', None)
        today = date.today()

        # 1. Fechar o histórico de clubes anterior do jogador
        JogadorHistoricoClube.objects.filter(
            jogador=req.jogador,
            data_fim__isnull=True
        ).update(data_fim=today)

        # 2. Atualizar o modelo de negócio Player
        if player:
            player.clube_profile = req.clube
            player.save(update_fields=['clube_profile'])

        # 3. Criar novo registro histórico
        JogadorHistoricoClube.objects.create(
            jogador=req.jogador,
            clube=req.clube,
            data_inicio=today,
            numero_camisola=getattr(player, 'number', None) or getattr(req.jogador, 'jersey_number', None)
        )

    return req
