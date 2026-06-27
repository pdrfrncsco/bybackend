from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from core.models import Tenant
from clubs.models import Club
from jogadores.models import Player
from accounts.models import (
    UserRole,
    OrganizacaoProfile,
    ClubeProfile,
    JogadorProfile,
    AdeptoProfile,
)
from accounts.services import (
    create_organizacao_profile,
    create_clube_profile,
    create_jogador_profile,
    create_adepto_profile,
)

User = get_user_model()


class ProfileServicesTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='password123',
            name='User One'
        )

    def test_create_organizacao_profile_service(self):
        profile = create_organizacao_profile(
            user=self.user,
            nome='Liga de Teste',
            sigla='LT',
            descricao='Uma liga de teste',
            email='liga@teste.com'
        )
        self.assertEqual(OrganizacaoProfile.objects.count(), 1)
        self.assertEqual(profile.nome, 'Liga de Teste')
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, UserRole.ORGANIZACAO)

    def test_create_clube_profile_service(self):
        profile = create_clube_profile(
            user=self.user,
            nome='Futebol Clube do Teste',
            sigla='FCT',
            estadio='Estádio Municipal'
        )
        self.assertEqual(ClubeProfile.objects.count(), 1)
        self.assertEqual(profile.nome, 'Futebol Clube do Teste')
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, UserRole.CLUBE)

    def test_create_jogador_profile_service(self):
        profile = create_jogador_profile(
            user=self.user,
            nome_completo='Jogador de Teste Silva',
            nome_desportivo='Silva',
            posicao='Avançado'
        )
        self.assertEqual(JogadorProfile.objects.count(), 1)
        self.assertEqual(profile.nome_completo, 'Jogador de Teste Silva')
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, UserRole.JOGADOR)

    def test_create_adepto_profile_service(self):
        profile = create_adepto_profile(
            user=self.user,
            nome='Adepto de Teste',
            cidade='Luanda'
        )
        self.assertEqual(AdeptoProfile.objects.count(), 1)
        self.assertEqual(profile.nome, 'Adepto de Teste')
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, UserRole.ADEPTO)


class ProfileAPITests(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            password='password123',
            role=UserRole.ADMIN
        )
        self.user1 = User.objects.create_user(
            username='player1',
            email='player1@example.com',
            password='password123',
            role=UserRole.JOGADOR
        )
        self.user2 = User.objects.create_user(
            username='player2',
            email='player2@example.com',
            password='password123',
            role=UserRole.JOGADOR
        )
        
        # Create profiles
        self.profile1 = create_jogador_profile(
            user=self.user1,
            nome_completo='Jogador Um',
            nome_desportivo='J1'
        )
        self.profile2 = create_jogador_profile(
            user=self.user2,
            nome_completo='Jogador Dois',
            nome_desportivo='J2'
        )

    def test_list_jogador_profiles(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('jogador-profile-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify that it listed the profiles
        if isinstance(response.data, dict):
            self.assertEqual(len(response.data.get('results', [])), 2)
        else:
            self.assertEqual(len(response.data), 2)

    def test_update_own_jogador_profile(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('jogador-profile-detail', kwargs={'pk': self.profile1.id})
        data = {'nome_completo': 'Jogador Um Atualizado'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile1.refresh_from_db()
        self.assertEqual(self.profile1.nome_completo, 'Jogador Um Atualizado')

    def test_cannot_update_other_jogador_profile(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('jogador-profile-detail', kwargs={'pk': self.profile2.id})
        data = {'nome_completo': 'Jogador Dois Tentativa'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_update_any_jogador_profile(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('jogador-profile-detail', kwargs={'pk': self.profile2.id})
        data = {'nome_completo': 'Jogador Dois Modificado por Admin'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile2.refresh_from_db()
        self.assertEqual(self.profile2.nome_completo, 'Jogador Dois Modificado por Admin')


class ProfileIntegrationTests(APITestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name='Tenant Angola', slug='angola')
        self.user_org = get_user_model().objects.create_user(
            username='org_user', email='org@example.com', password='password123', role=UserRole.ORGANIZACAO
        )
        self.user_clube = get_user_model().objects.create_user(
            username='clube_user', email='clube@example.com', password='password123', role=UserRole.CLUBE
        )
        
        self.org_profile = create_organizacao_profile(user=self.user_org, nome='FAF')
        self.clube_profile = create_clube_profile(user=self.user_clube, nome='Petro de Luanda')

    def test_club_linked_to_organizacao_profile(self):
        club = Club.objects.create(
            tenant=self.tenant,
            name='Petro de Luanda Club',
            acronym='PET',
            organizacao=self.org_profile
        )
        self.assertEqual(club.organizacao, self.org_profile)
        self.assertIn(club, self.org_profile.associated_clubs.all())

    def test_player_linked_to_clube_profile(self):
        club = Club.objects.create(
            tenant=self.tenant,
            name='Petro de Luanda Club',
            acronym='PET'
        )
        player = Player.objects.create(
            tenant=self.tenant,
            name='Geraldo',
            club=club,
            clube_profile=self.clube_profile
        )
        self.assertEqual(player.clube_profile, self.clube_profile)
        self.assertIn(player, self.clube_profile.associated_players.all())

