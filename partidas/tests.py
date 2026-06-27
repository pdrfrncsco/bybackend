from django.test import TestCase
from django.utils import timezone
from core.models import Tenant
from clubs.models import Club
from estadios.models import Stadium
from treinadores.models import Treinador, HistoricoTreinador
from .models import Match
from .serializers import MatchSerializer


class MatchSerializerTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name='Tenant', slug='tenant')
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

    def test_match_serializer_includes_team_details_and_names(self):
        match = Match.objects.create(
            tenant=self.tenant,
            tournament=None,
            home_team=self.home_club,
            away_team=self.away_club,
            home_score=2,
            away_score=1,
            date=timezone.now(),
            venue=self.stadium,
            status='scheduled',
            round='Jornada 1',
        )
        serializer = MatchSerializer(match)
        data = serializer.data

        self.assertEqual(data['home_team'], self.home_club.id)
        self.assertEqual(data['away_team'], self.away_club.id)

        self.assertIn('home_team_details', data)
        self.assertIn('away_team_details', data)
        self.assertEqual(data['home_team_details']['name'], 'Clube Casa')
        self.assertEqual(data['away_team_details']['name'], 'Clube Fora')
        self.assertIn('logo_url', data['home_team_details'])
        self.assertIn('logo_url', data['away_team_details'])

        self.assertEqual(data['home_team_name'], 'Clube Casa')
        self.assertEqual(data['away_team_name'], 'Clube Fora')

        self.assertIn('venue_details', data)
        self.assertEqual(data['venue_details']['name'], 'Estádio Principal')

    def test_home_coach_name_only_when_historico_matches_club_and_date(self):
        coach = Treinador.objects.create(
            tenant=self.tenant,
            first_name='João',
            last_name='Silva',
            nacionalidade='Angola',
            data_nascimento=timezone.now().date(),
            estilo_jogo='Ofensivo',
            biografia='Treinador experiente',
        )
        HistoricoTreinador.objects.create(
            treinador=coach,
            clube=self.home_club,
            cargo='Treinador Principal',
            data_inicio=timezone.now().date(),
        )
        match = Match.objects.create(
            tenant=self.tenant,
            tournament=None,
            home_team=self.home_club,
            away_team=self.away_club,
            home_score=0,
            away_score=0,
            date=timezone.now(),
            venue=self.stadium,
            status='scheduled',
            round='Jornada 1',
            home_coach=coach,
        )
        data = MatchSerializer(match).data
        self.assertEqual(data['home_coach_name'], 'João Silva')

    def test_home_coach_name_none_when_no_matching_historico(self):
        coach = Treinador.objects.create(
            tenant=self.tenant,
            first_name='Carlos',
            last_name='Pereira',
            nacionalidade='Angola',
            data_nascimento=timezone.now().date(),
            estilo_jogo='Defensivo',
            biografia='Treinador defensivo',
        )
        # Historico em outro clube ou sem historico não deve validar associação
        other_club = Club.objects.create(
            tenant=self.tenant,
            name='Outro Clube',
            founded_year=1999,
            location='Cidade',
            primary_color='#222222',
            secondary_color='#DDDDDD',
        )
        HistoricoTreinador.objects.create(
            treinador=coach,
            clube=other_club,
            cargo='Treinador Principal',
            data_inicio=timezone.now().date(),
        )
        match = Match.objects.create(
            tenant=self.tenant,
            tournament=None,
            home_team=self.home_club,
            away_team=self.away_club,
            home_score=0,
            away_score=0,
            date=timezone.now(),
            venue=self.stadium,
            status='scheduled',
            round='Jornada 2',
            home_coach=coach,
        )
        data = MatchSerializer(match).data
        self.assertIsNone(data['home_coach_name'])
