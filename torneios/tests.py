from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import Tenant
from usuarios.models import User
from clubs.models import Club
from estadios.models import Stadium
from partidas.models import Match
from .models import Tournament


class TournamentDetailSerializerTests(APITestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name='Tenant', slug='tenant')
        self.user = User.objects.create_user(
            username='manager',
            password='strongpassword123',
            tenant=self.tenant,
        )
        self.user.role = "manager"
        self.user.save()
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
        self.stadium = Stadium.objects.create(
            tenant=self.tenant,
            name='Estádio Principal',
            location='Cidade',
            capacity=10000,
        )
        self.tournament = Tournament.objects.create(
            tenant=self.tenant,
            name='Torneio Principal',
            season='2024/2025',
            start_date=timezone.now().date(),
            status='active',
        )
        self.tournament.clubs.add(self.home_club, self.away_club)

        self.match = Match.objects.create(
            tenant=self.tenant,
            tournament=self.tournament,
            home_team=self.home_club,
            away_team=self.away_club,
            home_score=2,
            away_score=1,
            date=timezone.now(),
            venue=self.stadium,
            status='scheduled',
            round='Jornada 1',
        )

        self.detail_url = reverse('tournament-detail', args=[self.tournament.id])

    def test_tournament_detail_includes_matches_with_team_details(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        self.assertIn('matches', data)
        self.assertEqual(len(data['matches']), 1)

        match_data = data['matches'][0]
        self.assertEqual(match_data['home_team'], self.home_club.id)
        self.assertEqual(match_data['away_team'], self.away_club.id)

        self.assertIn('home_team_details', match_data)
        self.assertIn('away_team_details', match_data)
        self.assertEqual(match_data['home_team_details']['name'], 'Clube Casa')
        self.assertEqual(match_data['away_team_details']['name'], 'Clube Fora')
        self.assertIn('logo_url', match_data['home_team_details'])
        self.assertIn('logo_url', match_data['away_team_details'])

        self.assertIn('home_team_name', match_data)
        self.assertIn('away_team_name', match_data)
        self.assertEqual(match_data['home_team_name'], 'Clube Casa')
        self.assertEqual(match_data['away_team_name'], 'Clube Fora')

        self.assertIn('venue_details', match_data)
        self.assertEqual(match_data['venue_details']['name'], 'Estádio Principal')

    def test_matches_are_ordered_by_round_number(self):
        Match.objects.create(
            tenant=self.tenant,
            tournament=self.tournament,
            home_team=self.home_club,
            away_team=self.away_club,
            home_score=0,
            away_score=0,
            date=timezone.now() + timezone.timedelta(days=1),
            venue=self.stadium,
            status='scheduled',
            round='Jornada 10',
        )
        Match.objects.create(
            tenant=self.tenant,
            tournament=self.tournament,
            home_team=self.home_club,
            away_team=self.away_club,
            home_score=0,
            away_score=0,
            date=timezone.now() + timezone.timedelta(days=2),
            venue=self.stadium,
            status='scheduled',
            round='Jornada 2',
        )

        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        rounds = [m['round'] for m in response.data['matches']]
        self.assertEqual(rounds, ['Jornada 1', 'Jornada 2', 'Jornada 10'])
