"""
BOLAYETU — Player Training History Service Tests

Tests for PlayerTrainingHistoryService methods.
"""

from django.test import TestCase
from datetime import date, timedelta

from players.models import Player, PlayerTrainingHistory
from players.services.training_service import (
    PlayerTrainingHistoryService,
    TrainingHistoryError,
)
from clubs.models import Club
from core.models import Tenant


class PlayerTrainingHistoryServiceTestCase(TestCase):
    """Test PlayerTrainingHistoryService methods."""

    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Org", slug="test-org")
        self.club = Club.objects.create(
            name="Test Academy",
            slug="test-academy",
            tenant=self.tenant,
        )
        self.player = Player.objects.create(
            first_name="Young",
            last_name="Player",
            date_of_birth=date(2005, 3, 20),
            nationality="AO",
            primary_position="CM",
        )

    def test_add_training_entry_with_club(self):
        """Test adding training history with a club."""
        entry = PlayerTrainingHistoryService.add_training_entry(
            player=self.player,
            start_date=date(2015, 1, 1),
            country="AO",
            training_category=PlayerTrainingHistory.TrainingCategory.YOUTH,
            club=self.club,
            end_date=date(2020, 12, 31),
        )

        self.assertEqual(entry.player, self.player)
        self.assertEqual(entry.club, self.club)
        self.assertEqual(entry.country, "AO")
        self.assertEqual(entry.training_category, PlayerTrainingHistory.TrainingCategory.YOUTH)
        self.assertFalse(entry.verified)

    def test_add_training_entry_with_academy_name(self):
        """Test adding training history with academy name instead of club."""
        entry = PlayerTrainingHistoryService.add_training_entry(
            player=self.player,
            start_date=date(2010, 1, 1),
            country="PT",
            training_category=PlayerTrainingHistory.TrainingCategory.ACADEMY,
            academy_name="Independent Soccer Academy",
            end_date=date(2014, 12, 31),
        )

        self.assertEqual(entry.player, self.player)
        self.assertIsNone(entry.club)
        self.assertEqual(entry.academy_name, "Independent Soccer Academy")

    def test_add_training_entry_requires_club_or_academy(self):
        """Test that either club or academy_name is required."""
        with self.assertRaises(TrainingHistoryError):
            PlayerTrainingHistoryService.add_training_entry(
                player=self.player,
                start_date=date(2015, 1, 1),
                country="AO",
            )

    def test_verify_training_entry(self):
        """Test verifying a training history entry."""
        entry = PlayerTrainingHistoryService.add_training_entry(
            player=self.player,
            start_date=date(2015, 1, 1),
            country="AO",
            club=self.club,
        )

        self.assertFalse(entry.verified)

        verified_entry = PlayerTrainingHistoryService.verify_training_entry(
            entry=entry,
            verified_by=None,
        )

        self.assertTrue(verified_entry.verified)
        self.assertIsNotNone(verified_entry.verified_at)

    def test_end_training_entry(self):
        """Test ending an ongoing training entry."""
        entry = PlayerTrainingHistoryService.add_training_entry(
            player=self.player,
            start_date=date(2020, 1, 1),
            country="AO",
            club=self.club,
        )

        self.assertIsNone(entry.end_date)

        ended_entry = PlayerTrainingHistoryService.end_training_entry(
            entry=entry,
            end_date=date.today(),
        )

        self.assertIsNotNone(ended_entry.end_date)

    def test_get_training_timeline(self):
        """Test getting complete training timeline."""
        # Add multiple entries
        PlayerTrainingHistoryService.add_training_entry(
            player=self.player,
            start_date=date(2010, 1, 1),
            country="AO",
            academy_name="First Academy",
            end_date=date(2012, 12, 31),
        )
        PlayerTrainingHistoryService.add_training_entry(
            player=self.player,
            start_date=date(2013, 1, 1),
            country="AO",
            club=self.club,
        )

        timeline = PlayerTrainingHistoryService.get_training_timeline(self.player)
        self.assertEqual(len(timeline), 2)
        # Should be ordered by start_date ascending
        self.assertEqual(timeline[0].start_date, date(2010, 1, 1))

    def test_get_training_years_by_club(self):
        """Test calculating total training years at a club."""
        # Add training entry for 5 years
        PlayerTrainingHistoryService.add_training_entry(
            player=self.player,
            start_date=date(2015, 1, 1),
            country="AO",
            club=self.club,
            end_date=date(2020, 1, 1),  # ~5 years
        )

        years = PlayerTrainingHistoryService.get_training_years_by_club(
            player=self.player,
            club_id=str(self.club.id),
        )

        self.assertAlmostEqual(years, 5.0, places=1)

    def test_get_training_compensation_data(self):
        """Test getting training compensation data."""
        PlayerTrainingHistoryService.add_training_entry(
            player=self.player,
            start_date=date(2010, 1, 1),
            country="AO",
            academy_name="Academy A",
            end_date=date(2013, 12, 31),
        )
        PlayerTrainingHistoryService.add_training_entry(
            player=self.player,
            start_date=date(2014, 1, 1),
            country="AO",
            club=self.club,
            training_category=PlayerTrainingHistory.TrainingCategory.PROFESSIONAL,
        )

        data = PlayerTrainingHistoryService.get_training_compensation_data(self.player)

        self.assertIn("total_years", data)
        self.assertIn("clubs", data)
        self.assertGreater(data["total_years"], 0)
        self.assertEqual(len(data["clubs"]), 2)

    def test_import_training_history(self):
        """Test bulk import of training history."""
        training_data = [
            {
                "start_date": date(2010, 1, 1),
                "country": "AO",
                "academy_name": "Academy One",
                "end_date": date(2012, 12, 31),
            },
            {
                "start_date": date(2013, 1, 1),
                "country": "AO",
                "club_id": str(self.club.id),
                "training_category": PlayerTrainingHistory.TrainingCategory.YOUTH,
            },
        ]

        entries = PlayerTrainingHistoryService.import_training_history(
            player=self.player,
            training_data=training_data,
        )

        self.assertEqual(len(entries), 2)

    def test_overlapping_training_entries_rejected(self):
        """Test that overlapping entries for same club are rejected."""
        PlayerTrainingHistoryService.add_training_entry(
            player=self.player,
            start_date=date(2015, 1, 1),
            country="AO",
            club=self.club,
            end_date=date(2020, 12, 31),
        )

        # Try to add overlapping entry
        with self.assertRaises(TrainingHistoryError):
            PlayerTrainingHistoryService.add_training_entry(
                player=self.player,
                start_date=date(2018, 1, 1),
                country="AO",
                club=self.club,
                end_date=date(2022, 12, 31),
            )
