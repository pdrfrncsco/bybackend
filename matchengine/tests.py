from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import Tenant
from usuarios.models import User
from clubes.models import Club
from jogadores.models import Player
from partidas.models import Match


class MatchEngineToggleLineupTests(APITestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name='Tenant', slug='tenant')
        self.user = User.objects.create_user(
            username='manager',
            password='strongpassword123',
            tenant=self.tenant,
            role='manager',
        )
        self.client.force_authenticate(user=self.user)

        self.home_club = Club.objects.create(
            tenant=self.tenant,
            name='Clube Casa',
            founded_year=2000,
            location='Cidade',
            primary_color='#000000',
            secondary_color='#FFFFFF',
        )
        self.away_club = Club.objects.create(
            tenant=self.tenant,
            name='Clube Fora',
            founded_year=2001,
            location='Cidade',
            primary_color='#111111',
            secondary_color='#EEEEEE',
        )

        self.player_home = Player.objects.create(
            tenant=self.tenant,
            club=self.home_club,
            name='Jogador Casa 1',
            number=10,
            position='FW',
        )

        self.match = Match.objects.create(
            tenant=self.tenant,
            tournament=None,
            home_team=self.home_club,
            away_team=self.away_club,
            home_score=0,
            away_score=0,
            date='2025-01-01T15:00:00Z',
            status='scheduled',
            round='Jornada 1',
        )

        self.url_toggle = reverse('matchengine-match-toggle-lineup', args=[self.match.id])

    def test_toggle_lineup_creates_and_toggles_entry(self):
        payload = {
            'team_id': str(self.home_club.id),
            'player_id': str(self.player_home.id),
        }

        response = self.client.post(self.url_toggle, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('home_lineup', response.data)
        self.assertIn('away_lineup', response.data)

        home_lineup = response.data['home_lineup']
        self.assertEqual(len(home_lineup), 1)
        player_data = home_lineup[0]
        self.assertEqual(player_data['name'], 'Jogador Casa 1')
        self.assertEqual(player_data['number'], 10)
        self.assertEqual(player_data['position'], 'FW')
        self.assertFalse(player_data['is_starter'])

        response2 = self.client.post(self.url_toggle, payload, format='json')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        home_lineup2 = response2.data['home_lineup']
        self.assertEqual(len(home_lineup2), 1)
        player_data2 = home_lineup2[0]
        self.assertTrue(player_data2['is_starter'])
