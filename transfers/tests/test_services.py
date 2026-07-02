"""
BOLAYETU — Transfer Service Tests

Tests for TransferService business logic.
"""

from django.test import TestCase
from datetime import date

from transfers.models import Transfer
from transfers.services import (
    TransferService,
    TransferAlreadyProcessed,
    TransferNotApproved,
    TransferInvalidState,
)
from players.models import Player, PlayerRegistration
from clubs.models import Club
from competitions.models import Competition
from core.models import Tenant


class TransferServiceTestCase(TestCase):
    """Test TransferService."""

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

        # Create initial registration at origin club
        self.initial_registration = PlayerRegistration.objects.create(
            player=self.player,
            club=self.from_club,
            tenant=self.tenant,
            shirt_number=9,
            joined_date=date(2024, 1, 1),
            status="registered"
        )

    def test_create_club_to_club_transfer(self):
        """Test creating a club-to-club transfer request."""
        transfer = TransferService.create_transfer(
            player=self.player,
            to_club=self.to_club,
            to_tenant=self.tenant,
            joined_date=date(2026, 7, 1),
            from_club=self.from_club,
            from_tenant=self.tenant,
            shirt_number=10,
            fee=50000.00,
        )

        self.assertEqual(transfer.status, Transfer.TransferStatus.PENDING)
        self.assertEqual(transfer.player, self.player)
        self.assertEqual(transfer.from_club, self.from_club)
        self.assertEqual(transfer.to_club, self.to_club)

    def test_create_free_agent_transfer(self):
        """Test creating a free agent transfer (auto-completes)."""
        # Create a new player without a club
        free_agent = Player.objects.create(
            first_name="Carlos",
            last_name="Santos",
            slug="carlos-santos",
            date_of_birth=date(2000, 3, 20),
            nationality="PT",
            primary_position="cb"
        )

        transfer = TransferService.create_transfer(
            player=free_agent,
            to_club=self.to_club,
            to_tenant=self.tenant,
            joined_date=date(2026, 7, 1),
            from_club=None,
            from_tenant=None,
            shirt_number=5,
        )

        # Free agent transfers should auto-complete
        self.assertEqual(transfer.status, Transfer.TransferStatus.COMPLETED)
        self.assertIsNone(transfer.from_club)

        # Verify registration was created
        registration = PlayerRegistration.objects.filter(
            player=free_agent,
            club=self.to_club,
            status="registered"
        ).first()
        self.assertIsNotNone(registration)

    def test_create_transfer_without_active_registration_fails(self):
        """Test that creating a transfer without active registration at from_club fails."""
        new_player = Player.objects.create(
            first_name="Novo",
            last_name="Jogador",
            slug="novo-jogador",
            date_of_birth=date(2002, 1, 1),
            nationality="BR",
            primary_position="cm"
        )

        with self.assertRaises(TransferInvalidState):
            TransferService.create_transfer(
                player=new_player,
                to_club=self.to_club,
                to_tenant=self.tenant,
                joined_date=date(2026, 7, 1),
                from_club=self.from_club,
                from_tenant=self.tenant,
            )

    def test_approve_transfer(self):
        """Test approving a pending transfer."""
        transfer = TransferService.create_transfer(
            player=self.player,
            to_club=self.to_club,
            to_tenant=self.tenant,
            joined_date=date(2026, 7, 1),
            from_club=self.from_club,
            from_tenant=self.tenant,
        )

        self.assertEqual(transfer.status, Transfer.TransferStatus.PENDING)

        approved = TransferService.approve_transfer(transfer)
        self.assertEqual(approved.status, Transfer.TransferStatus.APPROVED)

    def test_approve_already_processed_transfer_fails(self):
        """Test that approving a non-pending transfer fails."""
        transfer = TransferService.create_transfer(
            player=self.player,
            to_club=self.to_club,
            to_tenant=self.tenant,
            joined_date=date(2026, 7, 1),
            from_club=self.from_club,
            from_tenant=self.tenant,
        )

        TransferService.approve_transfer(transfer)

        with self.assertRaises(TransferAlreadyProcessed):
            TransferService.approve_transfer(transfer)

    def test_reject_transfer(self):
        """Test rejecting a pending transfer."""
        transfer = TransferService.create_transfer(
            player=self.player,
            to_club=self.to_club,
            to_tenant=self.tenant,
            joined_date=date(2026, 7, 1),
            from_club=self.from_club,
            from_tenant=self.tenant,
        )

        rejected = TransferService.reject_transfer(transfer, "Player not for sale.")
        self.assertEqual(rejected.status, Transfer.TransferStatus.REJECTED)
        self.assertEqual(rejected.rejection_reason, "Player not for sale.")

    def test_complete_transfer(self):
        """Test completing an approved transfer."""
        transfer = TransferService.create_transfer(
            player=self.player,
            to_club=self.to_club,
            to_tenant=self.tenant,
            joined_date=date(2026, 7, 1),
            from_club=self.from_club,
            from_tenant=self.tenant,
            competition=self.competition,
            shirt_number=10,
        )

        TransferService.approve_transfer(transfer)
        completed = TransferService.complete_transfer(transfer)

        self.assertEqual(completed.status, Transfer.TransferStatus.COMPLETED)
        self.assertIsNotNone(completed.completed_date)

        # Verify old registration was deactivated
        self.initial_registration.refresh_from_db()
        self.assertEqual(self.initial_registration.status, "transferred")
        self.assertIsNotNone(self.initial_registration.left_date)

        # Verify new registration was created
        new_registration = PlayerRegistration.objects.filter(
            player=self.player,
            club=self.to_club,
            status="registered"
        ).first()
        self.assertIsNotNone(new_registration)
        self.assertEqual(new_registration.shirt_number, 10)

    def test_complete_non_approved_transfer_fails(self):
        """Test that completing a non-approved transfer fails."""
        transfer = TransferService.create_transfer(
            player=self.player,
            to_club=self.to_club,
            to_tenant=self.tenant,
            joined_date=date(2026, 7, 1),
            from_club=self.from_club,
            from_tenant=self.tenant,
        )

        # Try to complete without approving
        with self.assertRaises(TransferNotApproved):
            TransferService.complete_transfer(transfer)

    def test_cancel_transfer(self):
        """Test cancelling a pending transfer."""
        transfer = TransferService.create_transfer(
            player=self.player,
            to_club=self.to_club,
            to_tenant=self.tenant,
            joined_date=date(2026, 7, 1),
            from_club=self.from_club,
            from_tenant=self.tenant,
        )

        cancelled = TransferService.cancel_transfer(transfer)
        self.assertEqual(cancelled.status, Transfer.TransferStatus.REJECTED)
        self.assertIn("Cancelled", cancelled.rejection_reason)
