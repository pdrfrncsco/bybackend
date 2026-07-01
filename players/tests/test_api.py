"""
BOLAYETU — Player API Tests

Tests for public player endpoints.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date

from players.models import Player, PlayerRegistration
from clubs.models import Club
from competitions.models import Competition
from core.models import Tenant

User = get_user_model()


class PlayerListViewTestCase(TestCase):
    """Test GET /api/v1/players/"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create a tenant
        self.tenant = Tenant.objects.create(
            name="Test Org",
            slug="test-org"
        )
        
        # Create players
        self.player1 = Player.objects.create(
            first_name="John",
            last_name="Doe",
            slug="john-doe",
            date_of_birth=date(2000, 1, 15),
            nationality="PT",
            primary_position="st",
            status="active"
        )
        
        self.player2 = Player.objects.create(
            first_name="Jane",
            last_name="Smith",
            slug="jane-smith",
            date_of_birth=date(1998, 5, 20),
            nationality="GB",
            primary_position="gk",
            status="active"
        )
        
        # Inactive player (should not appear in list)
        self.player3 = Player.objects.create(
            first_name="Inactive",
            last_name="Player",
            slug="inactive-player",
            date_of_birth=date(2002, 3, 10),
            nationality="BR",
            primary_position="cm",
            status="retired"
        )
    
    def test_list_players(self):
        """Test listing active players."""
        response = self.client.get('/api/v1/players/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 2)
        self.assertEqual(len(response.data['data']['results']), 2)
        
        # Verify only active players are returned
        slugs = [p['slug'] for p in response.data['data']['results']]
        self.assertIn('john-doe', slugs)
        self.assertIn('jane-smith', slugs)
        self.assertNotIn('inactive-player', slugs)
    
    def test_filter_by_position(self):
        """Test filtering players by position."""
        response = self.client.get('/api/v1/players/?position=st')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 1)
        self.assertEqual(response.data['data']['results'][0]['slug'], 'john-doe')
    
    def test_filter_by_nationality(self):
        """Test filtering players by nationality."""
        response = self.client.get('/api/v1/players/?nationality=GB')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 1)
        self.assertEqual(response.data['data']['results'][0]['slug'], 'jane-smith')


class PlayerDetailViewTestCase(TestCase):
    """Test GET /api/v1/players/{slug}/"""
    
    def setUp(self):
        self.client = APIClient()
        
        self.tenant = Tenant.objects.create(
            name="Test Org",
            slug="test-org"
        )
        
        self.club = Club.objects.create(
            name="Test Club",
            slug="test-club",
            tenant=self.tenant
        )
        
        self.competition = Competition.objects.create(
            name="Test League",
            slug="test-league",
            tenant=self.tenant
        )
        
        self.player = Player.objects.create(
            first_name="John",
            last_name="Doe",
            slug="john-doe",
            date_of_birth=date(2000, 1, 15),
            nationality="PT",
            primary_position="st",
            height_cm=185,
            weight_kg=78,
            foot="right",
            status="active",
            total_matches=50,
            total_goals=25,
            total_assists=10
        )
        
        # Create a registration
        self.registration = PlayerRegistration.objects.create(
            player=self.player,
            club=self.club,
            competition=self.competition,
            tenant=self.tenant,
            shirt_number=10,
            joined_date=date(2022, 1, 1),
            status="registered",
            matches_played=40,
            goals=20,
            assists=8,
            yellow_cards=5,
            red_cards=0
        )
    
    def test_get_player_detail(self):
        """Test getting player details."""
        response = self.client.get('/api/v1/players/john-doe/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data['data']
        
        self.assertEqual(data['slug'], 'john-doe')
        self.assertEqual(data['full_name'], 'John Doe')
        self.assertEqual(data['nationality'], 'PT')
        self.assertEqual(data['primary_position'], 'st')  # enum lowercase
        self.assertEqual(data['height_cm'], 185)
        self.assertEqual(data['total_matches'], 50)
    
    def test_get_nonexistent_player(self):
        """Test getting a player that doesn't exist."""
        response = self.client.get('/api/v1/players/nonexistent/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class PlayerSearchViewTestCase(TestCase):
    """Test GET /api/v1/players/search/"""
    
    def setUp(self):
        self.client = APIClient()
        
        self.player1 = Player.objects.create(
            first_name="John",
            last_name="Doe",
            slug="john-doe",
            date_of_birth=date(2000, 1, 15),
            nationality="PT",
            primary_position="st",
            status="active"
        )
        
        self.player2 = Player.objects.create(
            first_name="Jonathan",
            last_name="Smith",
            slug="jonathan-smith",
            date_of_birth=date(1998, 5, 20),
            nationality="GB",
            primary_position="gk",
            status="active"
        )
        
        self.player3 = Player.objects.create(
            first_name="Maria",
            last_name="Johnson",
            slug="maria-johnson",
            date_of_birth=date(2002, 3, 10),
            nationality="BR",
            primary_position="cm",
            status="retired"
        )
    
    def test_search_by_first_name(self):
        """Test searching players by first name."""
        response = self.client.get('/api/v1/players/search/?q=john')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        slugs = [p['slug'] for p in response.data['data']]
        # "john" matches John Doe (first_name icontains)
        self.assertIn('john-doe', slugs)
        # Retired players should never appear
        self.assertNotIn('maria-johnson', slugs)
    
    def test_search_by_last_name(self):
        """Test searching players by last name."""
        response = self.client.get('/api/v1/players/search/?q=smith')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['slug'], 'jonathan-smith')
    
    def test_search_query_too_short(self):
        """Test that searches shorter than 2 chars return empty."""
        response = self.client.get('/api/v1/players/search/?q=a')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 0)
    
    def test_search_no_query(self):
        """Test search without query parameter."""
        response = self.client.get('/api/v1/players/search/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 0)
