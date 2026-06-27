from datetime import date
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from core.models import Tenant
from clubs.models import Club
from jogadores.models import Player
from accounts.models import UserRole
from accounts.services import (
    create_organizacao_profile,
    create_clube_profile,
    create_jogador_profile,
)
from affiliations.models import (
    ClubeOrganizacaoRequest,
    JogadorClubeRequest,
    JogadorHistoricoClube,
    RequestStatus,
)
from affiliations.services import (
    create_clube_organizacao_request,
    decide_clube_organizacao_request,
    create_jogador_clube_request,
    decide_jogador_clube_request,
)

User = get_user_model()


class AffiliationServicesTests(APITestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name='FAF', slug='faf')
        
        self.user_org = User.objects.create_user(
            username='org_user', email='org@example.com', password='password123', role=UserRole.ORGANIZACAO
        )
        self.user_club = User.objects.create_user(
            username='club_user', email='club@example.com', password='password123', role=UserRole.CLUBE
        )
        self.user_player = User.objects.create_user(
            username='player_user', email='player@example.com', password='password123', role=UserRole.JOGADOR
        )

        self.org_profile = create_organizacao_profile(user=self.user_org, nome='Associação de Futebol')
        self.club_profile = create_clube_profile(user=self.user_club, nome='1º de Agosto')
        self.player_profile = create_jogador_profile(user=self.user_player, nome_completo='Gelson Dala')

        # Business entities linked to profiles
        self.club_business = Club.objects.create(
            tenant=self.tenant,
            name='1º de Agosto Club',
            acronym='PRI',
            clube_profile=self.club_profile
        )
        self.player_business = Player.objects.create(
            tenant=self.tenant,
            name='Gelson Dala',
            club=self.club_business,
            jogador_profile=self.player_profile
        )

    def test_clube_organizacao_flow(self):
        # 1. Create request
        req = create_clube_organizacao_request(
            clube_profile=self.club_profile,
            organizacao_profile=self.org_profile,
            mensagem="Gostaríamos de participar no campeonato regional."
        )
        self.assertEqual(ClubeOrganizacaoRequest.objects.count(), 1)
        self.assertEqual(req.estado, RequestStatus.PENDING)

        # 2. Decide request (Approve)
        decide_clube_organizacao_request(
            request_id=req.id,
            status=RequestStatus.APPROVED,
            user_decisor=self.user_org,
            mensagem_resposta="Inscrição aprovada com sucesso."
        )

        req.refresh_from_db()
        self.assertEqual(req.estado, RequestStatus.APPROVED)
        
        # Verify Club business link was updated
        self.club_business.refresh_from_db()
        self.assertEqual(self.club_business.organizacao, self.org_profile)

    def test_jogador_clube_flow(self):
        # 1. Create request
        req = create_jogador_clube_request(
            jogador_profile=self.player_profile,
            clube_profile=self.club_profile,
            mensagem="Quero fazer testes no clube."
        )
        self.assertEqual(JogadorClubeRequest.objects.count(), 1)
        self.assertEqual(req.estado, RequestStatus.PENDING)

        # 2. Decide request (Approve)
        decide_jogador_clube_request(
            request_id=req.id,
            status=RequestStatus.APPROVED,
            user_decisor=self.user_club,
            mensagem_resposta="Bem-vindo ao plantel!"
        )

        req.refresh_from_db()
        self.assertEqual(req.estado, RequestStatus.APPROVED)

        # Verify Player business link was updated
        self.player_business.refresh_from_db()
        self.assertEqual(self.player_business.clube_profile, self.club_profile)

        # Verify Career History entry was created
        self.assertEqual(JogadorHistoricoClube.objects.count(), 1)
        history = JogadorHistoricoClube.objects.get()
        self.assertEqual(history.jogador, self.player_profile)
        self.assertEqual(history.clube, self.club_profile)
        self.assertEqual(history.data_inicio, date.today())
        self.assertIsNone(history.data_fim)

    def test_prevent_duplicate_pending_requests(self):
        create_clube_organizacao_request(self.club_profile, self.org_profile)
        with self.assertRaises(ValueError):
            create_clube_organizacao_request(self.club_profile, self.org_profile)


class AffiliationAPITests(APITestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name='FAF', slug='faf')
        self.user_club = User.objects.create_user(
            username='club_user', email='club@example.com', password='password123', role=UserRole.CLUBE
        )
        self.user_org = User.objects.create_user(
            username='org_user', email='org@example.com', password='password123', role=UserRole.ORGANIZACAO
        )
        self.club_profile = create_clube_profile(user=self.user_club, nome='Kabuscorp')
        self.org_profile = create_organizacao_profile(user=self.user_org, nome='APF')

    def test_create_clube_organizacao_request_api(self):
        self.client.force_authenticate(user=self.user_club)
        url = reverse('clube-organizacao-request-list')
        data = {
            'clube': str(self.club_profile.id),
            'organizacao': str(self.org_profile.id),
            'mensagem': 'Solicitação FAF.'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ClubeOrganizacaoRequest.objects.count(), 1)

    def test_decide_clube_organizacao_request_api(self):
        req = create_clube_organizacao_request(self.club_profile, self.org_profile)
        
        self.client.force_authenticate(user=self.user_org)
        url = reverse('clube-organizacao-request-decide', kwargs={'pk': req.id})
        data = {
            'estado': RequestStatus.APPROVED,
            'mensagem_resposta': 'Aceite.'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        req.refresh_from_db()
        self.assertEqual(req.estado, RequestStatus.APPROVED)
