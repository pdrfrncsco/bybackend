"""
BOLAYETU — Transfer Model Tests

Tests for Transfer model.
"""

from django.test import TestCase
from datetime import date

from transfers.models import Transfer
from players.models import Player
from clubs.models import Club
from competitions.models import Competition
from core.models import Tenant


class TransferModelTestCase(TestCase):
    """Test Transfer model."""

    def setUp(self):
        self.tenant = Tenant.objects.create(
            name="Test Federation",
            slug="test-federation"
        )

        self.from_club = Club.objects.create(
            name="Origin Club",
            slug="origin-club",
            tenant=self.tenant
        )

        self.to_club = Club.objects.create(
            name="Destination Club",
            slug="destination-club",
            tenant=self.tenant
        )

        self.competition = Competition.objects.create(
            name="Test League",
            slug="test-league",
            tenant=self.tenant
        )

        self.player = Player.objects.create(
            first_name="João",
            last_name="Silva",
            slug="joao-silva",
            date_of_birth=date(1998, 5, 15),
            nationality="AO",
            primary_position="st"
        )

    def test_create_transfer(self):
        """Test creating a club-to-club transfer."""
        transfer = Transfer.objects.create(
            player=self.player,
            from_club=self.from_club,
            to_club=self.to_club,
            from_tenant=self.tenant,
            to_tenant=self.tenant,
            competition=self.competition,
            joined_date=date(2026, 7, 1),
            shirt_number=10,
            fee=50000.00,
            status=Transfer.TransferStatus.PENDING,
        )

        self.assertEqual(transfer.player, self.player)
        self.assertEqual(transfer.from_club, self.from_club)
        self.assertEqual(transfer.to_club, self.to_club)
        self.assertEqual(transfer.status, "pending")
        self.assertEqual(transfer.fee, 50000.00)

    def test_create_free_agent_transfer(self):
        """Test creating a free agent transfer (no from_club)."""
        transfer = Transfer.objects.create(
            player=self.player,
            from_club=None,  # Free agent
            to_club=self.to_club,
            from_tenant=None,
            to_tenant=self.tenant,
            joined_date=date(2026, 7, 1),
            status=Transfer.TransferStatus.COMPLETED,
        )

        self.assertIsNone(transfer.from_club)
        self.assertEqual(transfer.to_club, self.to_club)
        self.assertEqual(transfer.status, "completed")

    def test_transfer_str_representation(self):
        """Test string representation of transfer."""
        transfer = Transfer.objects.create(
            player=self.player,
            from_club=self.from_club,
            to_club=self.to_club,
            from_tenant=self.tenant,
            to_tenant=self.tenant,
            joined_date=date(2026, 7, 1),
            status=Transfer.TransferStatus.PENDING,
        )

        expected = f"Transfer of {self.player.full_name}: {self.from_club.name} → {self.to_club.name} (pending)"
        self.assertEqual(str(transfer), expected)

    def test_free_agent_transfer_str(self):
        """Test string representation of free agent transfer."""
        transfer = Transfer.objects.create(
            player=self.player,
            from_club=None,
            to_club=self.to_club,
            from_tenant=None,
            to_tenant=self.tenant,
            joined_date=date(2026, 7, 1),
            status=Transfer.TransferStatus.COMPLETED,
        )

        expected = f"Transfer of {self.player.full_name}: Free Agent → {self.to_club.name} (completed)"
        self.assertEqual(str(transfer), expected)

    def test_transfer_status_choices(self):
        """Test that transfer status choices are valid."""
        valid_statuses = ["pending", "approved", "rejected", "completed"]
        for status in valid_statuses:
            transfer = Transfer.objects.create(
                player=self.player,
                from_club=self.from_club,
                to_club=self.to_club,
                from_tenant=self.tenant,
                to_tenant=self.tenant,
                joined_date=date(2026, 7, 1),
                status=status,
            )
            self.assertEqual(transfer.status, status)

    def test_transfer_default_status(self):
        """Test that default status is pending."""
        transfer = Transfer.objects.create(
            player=self.player,
            from_club=self.from_club,
            to_club=self.to_club,
            from_tenant=self.tenant,
            to_tenant=self.tenant,
            joined_date=date(2026, 7, 1),
        )

        self.assertEqual(transfer.status, Transfer.TransferStatus.PENDING)
