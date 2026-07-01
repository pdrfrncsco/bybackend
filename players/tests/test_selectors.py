"""
BOLAYETU — Player Selector Tests

Tests for PlayerSelector read queries.
"""

from django.test import TestCase
from datetime import date

from players.models import Player, PlayerRegistration
from players.selectors import PlayerSelector, PlayerRegistrationSelector
from clubs.models import Club
from competitions.models import Competition
from core.models import Tenant


class PlayerSelectorTestCase(TestCase):
    """Test PlayerSelector queries."""
    
    def setUp(self):
        self.player1 = Player.objects.create(
            first_name="John",
            last_name="Doe",
            slug="john-doe",
            date_of_birth=date(2000, 1, 15),
            nationality="PT",
            primary_position="ST",
            status="active"
        )
        
        self.player2 = Player.objects.create(
            first_name="Maria",
            last_name="Silva",
            slug="maria-silva",
            date_of_birth=date(1998, 5, 20),
            nationality="BR",
            primary_position="GK",
            status="active"
        )
        
        self.player3 = Player.objects.create(
            first_name="Inactive",
            last_name="Player",
            slug="inactive-player",
            date_of_birth=date(2002, 3, 10),
            nationality="PT",
            primary_position="MF",
            status="retired"
        )
    
    def test_get_by_id(self):
        """Test get_by_id selector."""
        player = PlayerSelector.get_by_id(self.player1.id)
        self.assertEqual(player.slug, "john-doe")
    
    def test_get_by_id_not_found(self):
        """Test get_by_id returns None for nonexistent player."""
        player = PlayerSelector.get_by_id(99999)
        self.assertIsNone(player)
    
    def test_get_by_slug(self):
        """Test get_by_slug selector."""
        player = PlayerSelector.get_by_slug("john-doe")
        self.assertEqual(player.id, self.player1.id)
    
    def test_get_by_slug_not_found(self):
        """Test get_by_slug returns None for nonexistent slug."""
        player = PlayerSelector.get_by_slug("nonexistent")
        self.assertIsNone(player)
    
    def test_list_active(self):
        """Test list_active returns only active players."""
        players = PlayerSelector.list_active()
        
        self.assertEqual(players.count(), 2)
        slugs = [p.slug for p in players]
        self.assertIn("john-doe", slugs)
        self.assertIn("maria-silva", slugs)
        self.assertNotIn("inactive-player", slugs)
    
    def test_search(self):
        """Test search by name."""
        players = PlayerSelector.search("maria")
        
        self.assertEqual(players.count(), 1)
        self.assertEqual(players.first().slug, "maria-silva")
    
    def test_search_case_insensitive(self):
        """Test search is case insensitive."""
        players = PlayerSelector.search("JOHN")
        
        self.assertEqual(players.count(), 1)
        self.assertEqual(players.first().slug, "john-doe")
    
    def test_list_by_position(self):
        """Test list_by_position."""
        players = PlayerSelector.list_by_position("ST")
        
        self.assertEqual(players.count(), 1)
        self.assertEqual(players.first().slug, "john-doe")
    
    def test_list_by_nationality(self):
        """Test list_by_nationality."""
        players = PlayerSelector.list_by_nationality("PT")
        
        self.assertEqual(players.count(), 1)
        self.assertEqual(players.first().slug, "john-doe")


class PlayerRegistrationSelectorTestCase(TestCase):
    """Test PlayerRegistrationSelector queries."""
    
    def setUp(self):
        self.tenant = Tenant.objects.create(
            name="Test Org",
            slug="test-org"
        )
        
        self.club1 = Club.objects.create(
            name="Test Club 1",
            slug="test-club-1",
            tenant=self.tenant
        )
        
        self.club2 = Club.objects.create(
            name="Test Club 2",
            slug="test-club-2",
            tenant=self.tenant
        )
        
        self.competition = Competition.objects.create(
            name="Test League",
            slug="test-league",
            tenant=self.tenant
        )
        
        self.player1 = Player.objects.create(
            first_name="John",
            last_name="Doe",
            slug="john-doe",
            date_of_birth=date(2000, 1, 15),
            nationality="PT",
            primary_position="ST"
        )
        
        self.player2 = Player.objects.create(
            first_name="Maria",
            last_name="Silva",
            slug="maria-silva",
            date_of_birth=date(1998, 5, 20),
            nationality="BR",
            primary_position="GK"
        )
        
        # Current registration
        self.reg1 = PlayerRegistration.objects.create(
            player=self.player1,
            club=self.club1,
            competition=self.competition,
            tenant=self.tenant,
            shirt_number=10,
            joined_date=date(2022, 1, 1),
            status="registered"
        )
        
        # Transferred registration
        self.reg2 = PlayerRegistration.objects.create(
            player=self.player1,
            club=self.club2,
            competition=self.competition,
            tenant=self.tenant,
            shirt_number=15,
            joined_date=date(2023, 1, 1),
            left_date=date(2024, 1, 1),
            status="transferred"
        )
        
        # Another player's registration
        self.reg3 = PlayerRegistration.objects.create(
            player=self.player2,
            club=self.club1,
            competition=self.competition,
            tenant=self.tenant,
            shirt_number=1,
            joined_date=date(2020, 1, 1),
            status="registered"
        )
    
    def test_get_current_registration(self):
        """Test get_current_registration."""
        reg = PlayerRegistrationSelector.get_current_registration(self.player1.id)
        
        self.assertEqual(reg.id, self.reg1.id)
        self.assertEqual(reg.status, "registered")
    
    def test_list_by_club(self):
        """Test list_by_club."""
        registrations = PlayerRegistrationSelector.list_by_club(self.club1.id)
        
        self.assertEqual(registrations.count(), 2)
        ids = [r.id for r in registrations]
        self.assertIn(self.reg1.id, ids)
        self.assertIn(self.reg3.id, ids)
    
    def test_list_by_competition(self):
        """Test list_by_competition."""
        registrations = PlayerRegistrationSelector.list_by_competition(self.competition.id)
        
        # Should only include "registered" status
        self.assertEqual(registrations.count(), 2)
        statuses = [r.status for r in registrations]
        self.assertNotIn("transferred", statuses)
    
    def test_list_career(self):
        """Test list_career includes all registrations."""
        career = PlayerRegistrationSelector.list_career(self.player1.id)
        
        self.assertEqual(career.count(), 2)
        ids = [r.id for r in career]
        self.assertIn(self.reg1.id, ids)
        self.assertIn(self.reg2.id, ids)
