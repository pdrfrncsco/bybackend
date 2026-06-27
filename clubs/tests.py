from django.test import TestCase
from django.core.management import call_command
from core.models import Tenant
from jogadores.models import Player
from .models import Club
from .serializers import ClubSerializer, ClubBasicSerializer, ClubListSerializer


class ClubSerializerTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name='Tenant', slug='tenant')

    def test_club_serializer_includes_logo_url_field(self):
        club = Club.objects.create(
            tenant=self.tenant,
            name='Clube Teste',
            founded_year=2000,
            location='Cidade',
            primary_color='#000000',
            secondary_color='#FFFFFF',
        )
        serializer = ClubSerializer(club)
        data = serializer.data
        self.assertIn('logo_url', data)

    def test_club_basic_serializer_structure_for_nested_usage(self):
        club = Club.objects.create(
            tenant=self.tenant,
            name='Clube Nested',
            founded_year=1999,
            location='Cidade',
            primary_color='#111111',
            secondary_color='#EEEEEE',
        )
        serializer = ClubBasicSerializer(club)
        data = serializer.data
        self.assertEqual(data['id'], str(club.id))
        self.assertEqual(data['name'], 'Clube Nested')
        self.assertIn('logo_url', data)
        self.assertEqual(data['primary_color'], '#111111')
        self.assertEqual(data['secondary_color'], '#EEEEEE')

    def test_club_serializer_active_players_counts_only_active_status(self):
        club = Club.objects.create(
            tenant=self.tenant,
            name='Clube Players',
            founded_year=2001,
            location='Cidade',
        )
        Player.objects.create(tenant=self.tenant, club=club, name='Jogador 1', status='active')
        Player.objects.create(tenant=self.tenant, club=club, name='Jogador 2', status='injured')
        Player.objects.create(tenant=self.tenant, club=club, name='Jogador 3', status='active')

        serializer = ClubSerializer(club)
        data = serializer.data
        self.assertIn('active_players', data)
        self.assertEqual(data['active_players'], 2)

    def test_club_list_serializer_active_players_counts_only_active_status(self):
        club = Club.objects.create(
            tenant=self.tenant,
            name='Clube Lista',
            founded_year=2002,
            location='Cidade',
        )
        Player.objects.create(tenant=self.tenant, club=club, name='Jogador 1', status='active')
        Player.objects.create(tenant=self.tenant, club=club, name='Jogador 2', status='suspended')

        serializer = ClubListSerializer(club)
        data = serializer.data
        self.assertIn('active_players', data)
        self.assertEqual(data['active_players'], 1)


class SeedAngolaCommandTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name='Federação Angolana', slug='angola')

    def test_seed_angola_creates_clubs_and_players_idempotent(self):
        call_command('seed_angola', tenant_slug=self.tenant.slug)
        clubs_first = list(Club.objects.filter(tenant=self.tenant).values_list('id', flat=True))
        self.assertGreaterEqual(len(clubs_first), 5)

        call_command('seed_angola', tenant_slug=self.tenant.slug)
        clubs_second = list(Club.objects.filter(tenant=self.tenant).values_list('id', flat=True))

        self.assertEqual(len(clubs_first), len(clubs_second))
