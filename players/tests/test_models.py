"""
BOLAYETU — Player Model Tests

Tests for Player and PlayerRegistration models.
"""

from django.test import TestCase
from django.utils import timezone
from datetime import date, timedelta

from players.models import Player, PlayerRegistration
from clubs.models import Club
from competitions.models import Competition
from core.models import Tenant


class PlayerModelTestCase(TestCase):
    """Test Player model."""
    
    def test_create_player(self):
        """Test creating a player."""
        player = Player.objects.create(
            first_name="John",
            last_name="Doe",
            slug="john-doe",
            date_of_birth=date(2000, 1, 15),
            nationality="PT",
            primary_position="ST"
        )
        
        self.assertEqual(player.first_name, "John")
        self.assertEqual(player.last_name, "Doe")
        self.assertEqual(player.slug, "john-doe")
        self.assertEqual(player.status, "active")
    
    def test_player_full_name(self):
        """Test full_name property."""
        player = Player.objects.create(
            first_name="John",
            last_name="Doe",
            slug="john-doe",
            date_of_birth=date(2000, 1, 15),
            nationality="PT",
            primary_position="ST"
        )
        
        self.assertEqual(player.full_name, "John Doe")
    
    def test_player_age_calculation(self):
        """Test age property."""
        # Use a fixed date: player born on 2000-01-15
        player = Player.objects.create(
            first_name="John",
            last_name="Doe",
            slug="john-doe",
            date_of_birth=date(2000, 1, 15),
            nationality="PT",
            primary_position="ST"
        )
        
        # Age should be at least 23 (as of 2024)
        self.assertGreater(player.age, 20)
    
    def test_player_slug_uniqueness(self):
        """Test that player slugs are unique."""
        Player.objects.create(
            first_name="John",
            last_name="Doe",
            slug="john-doe",
            date_of_birth=date(2000, 1, 15),
            nationality="PT",
            primary_position="ST"
        )
        
        with self.assertRaises(Exception):
            Player.objects.create(
                first_name="John",
                last_name="Doe2",
                slug="john-doe",
                date_of_birth=date(2001, 1, 15),
                nationality="PT",
                primary_position="ST"
            )


class PlayerRegistrationModelTestCase(TestCase):
    """Test PlayerRegistration model."""
    
    def setUp(self):
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
            primary_position="ST"
        )
    
    def test_create_registration(self):
        """Test creating a player registration."""
        registration = PlayerRegistration.objects.create(
            player=self.player,
            club=self.club,
            competition=self.competition,
            tenant=self.tenant,
            shirt_number=10,
            joined_date=date(2022, 1, 1),
            status="registered"
        )
        
        self.assertEqual(registration.player, self.player)
        self.assertEqual(registration.club, self.club)
        self.assertEqual(registration.shirt_number, 10)
        self.assertEqual(registration.status, "registered")
    
    def test_unique_active_registration(self):
        """Test that only one active registration per player-club-competition is allowed."""
        PlayerRegistration.objects.create(
            player=self.player,
            club=self.club,
            competition=self.competition,
            tenant=self.tenant,
            shirt_number=10,
            joined_date=date(2022, 1, 1),
            status="registered"
        )
        
        # Attempting to create another "registered" registration for same player-club-competition should fail
        with self.assertRaises(Exception):
            PlayerRegistration.objects.create(
                player=self.player,
                club=self.club,
                competition=self.competition,
                tenant=self.tenant,
                shirt_number=15,
                joined_date=date(2023, 1, 1),
                status="registered"
            )
    
    def test_multiple_loaned_registrations(self):
        """Test that 'transferred' status allows duplicates (soft delete)."""
        club2 = Club.objects.create(
            name="Test Club 2",
            slug="test-club-2",
            tenant=self.tenant
        )
        
        reg1 = PlayerRegistration.objects.create(
            player=self.player,
            club=self.club,
            competition=self.competition,
            tenant=self.tenant,
            shirt_number=10,
            joined_date=date(2022, 1, 1),
            status="registered"
        )
        
        # Transfer to new club by marking old as transferred
        reg1.status = "transferred"
        reg1.left_date = date(2023, 1, 1)
        reg1.save()
        
        # Now can create new active registration
        reg2 = PlayerRegistration.objects.create(
            player=self.player,
            club=club2,
            competition=self.competition,
            tenant=self.tenant,
            shirt_number=7,
            joined_date=date(2023, 1, 1),
            status="registered"
        )
        
        self.assertNotEqual(reg1.id, reg2.id)
        self.assertEqual(reg2.status, "registered")
