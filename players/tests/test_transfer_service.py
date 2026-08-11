"""
BOLAYETU — Player Transfer Service Tests

Tests for PlayerTransferService methods.
"""

from django.test import TestCase
from datetime import date, timedelta

from players.models import Player, PlayerRegistration, PlayerContract, PlayerCareer
from players.services.transfer_service import (
    PlayerTransferService,
    TransferError,
)
from players.services import PlayerRegistrationService
from clubs.models import Club
from core.models import Tenant


class PlayerTransferServiceTestCase(TestCase):
    """Test PlayerTransferService methods."""

    def setUp(self):
        self.tenant1 = Tenant.objects.create(name="Club One Org", slug="club-one-org")
        self.tenant2 = Tenant.objects.create(name="Club Two Org", slug="club-two-org")

        self.club1 = Club.objects.create(
            name="Origin Club",
            slug="origin-club",
            tenant=self.tenant1,
        )
        self.club2 = Club.objects.create(
            name="Destination Club",
            slug="destination-club",
            tenant=self.tenant2,
        )

        self.player = Player.objects.create(
            first_name="Transfer",
            last_name="Player",
            date_of_birth=date(1998, 7, 10),
            nationality="AO",
            primary_position="CF",
        )

    def test_execute_transfer(self):
        """Test executing a complete transfer."""
        # Register player at origin club first
        old_registration = PlayerRegistrationService.register_player(
            player=self.player,
            club=self.club1,
            tenant=self.tenant1,
            joined_date=date(2020, 1, 1),
        )

        self.assertEqual(old_registration.status, PlayerRegistration.RegistrationStatus.REGISTERED)

        # Execute transfer
        result = PlayerTransferService.execute_transfer(
            player=self.player,
            from_club=self.club1,
            to_club=self.club2,
            to_tenant=self.tenant2,
            joined_date=date.today(),
            shirt_number=9,
            transfer_fee=50000.00,
        )

        # Verify old registration was deactivated
        old_registration.refresh_from_db()
        self.assertEqual(old_registration.status, PlayerRegistration.RegistrationStatus.TRANSFERRED)

        # Verify new registration was created
        self.assertIsNotNone(result["new_registration"])
        self.assertEqual(result["new_registration"].club, self.club2)
        self.assertEqual(result["new_registration"].shirt_number, 9)

    def test_execute_transfer_free_agent(self):
        """Test transferring a free agent (no origin club)."""
        result = PlayerTransferService.execute_transfer(
            player=self.player,
            from_club=None,
            to_club=self.club1,
            to_tenant=self.tenant1,
            joined_date=date.today(),
        )

        # No old registration
        self.assertIsNone(result["old_registration"])

        # New registration created
        self.assertIsNotNone(result["new_registration"])
        self.assertEqual(result["new_registration"].club, self.club1)

    def test_execute_transfer_with_contract(self):
        """Test transfer also terminates old contract and creates new one."""
        # Create old registration and contract
        old_registration = PlayerRegistrationService.register_player(
            player=self.player,
            club=self.club1,
            tenant=self.tenant1,
            joined_date=date(2020, 1, 1),
        )

        old_contract = PlayerContract.objects.create(
            player=self.player,
            club=self.club1,
            tenant=self.tenant1,
            contract_type=PlayerContract.ContractType.PROFESSIONAL,
            status=PlayerContract.ContractStatus.ACTIVE,
            start_date=date(2020, 1, 1),
            end_date=date(2025, 12, 31),
        )

        # Execute transfer with new contract data
        result = PlayerTransferService.execute_transfer(
            player=self.player,
            from_club=self.club1,
            to_club=self.club2,
            to_tenant=self.tenant2,
            joined_date=date.today(),
            new_contract_data={
                "contract_type": PlayerContract.ContractType.PROFESSIONAL,
                "start_date": date.today(),
                "end_date": date.today() + timedelta(days=365 * 3),
                "salary": 10000.00,
                "currency": "USD",
            },
        )

        # Verify old contract was terminated
        old_contract.refresh_from_db()
        self.assertEqual(old_contract.status, PlayerContract.ContractStatus.TERMINATED)

        # Verify new contract was created
        self.assertIsNotNone(result["new_contract"])
        self.assertEqual(result["new_contract"].club, self.club2)
        self.assertEqual(result["new_contract"].salary, 10000.00)

    def test_release_player(self):
        """Test releasing a player from a club."""
        # Register player
        registration = PlayerRegistrationService.register_player(
            player=self.player,
            club=self.club1,
            tenant=self.tenant1,
            joined_date=date(2020, 1, 1),
        )

        # Release player
        result = PlayerTransferService.release_player(
            player=self.player,
            from_club=self.club1,
            release_date=date.today(),
            reason="Mutual agreement",
        )

        # Verify registration was deactivated
        registration.refresh_from_db()
        self.assertEqual(registration.status, PlayerRegistration.RegistrationStatus.TRANSFERRED)

    def test_release_player_not_registered(self):
        """Test releasing a player who is not registered at the club."""
        with self.assertRaises(TransferError):
            PlayerTransferService.release_player(
                player=self.player,
                from_club=self.club1,
            )

    def test_start_loan(self):
        """Test starting a loan."""
        # Register player at origin club
        original_registration = PlayerRegistrationService.register_player(
            player=self.player,
            club=self.club1,
            tenant=self.tenant1,
            joined_date=date(2020, 1, 1),
        )

        # Start loan
        result = PlayerTransferService.start_loan(
            player=self.player,
            from_club=self.club1,
            to_club=self.club2,
            to_tenant=self.tenant2,
            loan_start_date=date.today(),
            loan_end_date=date.today() + timedelta(days=180),
            shirt_number=10,
        )

        # Verify original registration is marked as LOANED
        original_registration.refresh_from_db()
        self.assertEqual(original_registration.status, PlayerRegistration.RegistrationStatus.LOANED)

        # Verify loan registration was created
        self.assertIsNotNone(result["loan_registration"])
        self.assertEqual(result["loan_registration"].club, self.club2)
        self.assertEqual(result["loan_registration"].status, PlayerRegistration.RegistrationStatus.LOANED)

    def test_start_loan_not_registered(self):
        """Test starting loan for player not registered at origin club."""
        with self.assertRaises(TransferError):
            PlayerTransferService.start_loan(
                player=self.player,
                from_club=self.club1,
                to_club=self.club2,
                to_tenant=self.tenant2,
                loan_start_date=date.today(),
                loan_end_date=date.today() + timedelta(days=180),
            )

    def test_end_loan(self):
        """Test ending a loan."""
        # Setup: register and loan player
        original_registration = PlayerRegistrationService.register_player(
            player=self.player,
            club=self.club1,
            tenant=self.tenant1,
            joined_date=date(2020, 1, 1),
        )

        loan_result = PlayerTransferService.start_loan(
            player=self.player,
            from_club=self.club1,
            to_club=self.club2,
            to_tenant=self.tenant2,
            loan_start_date=date.today() - timedelta(days=90),
            loan_end_date=date.today(),
        )

        # End loan
        ended_loan = PlayerTransferService.end_loan(
            player=self.player,
            loan_club=self.club2,
        )

        # Verify loan registration is deactivated
        self.assertEqual(ended_loan.status, PlayerRegistration.RegistrationStatus.TRANSFERRED)

        # Verify original registration is back to REGISTERED
        original_registration.refresh_from_db()
        self.assertEqual(original_registration.status, PlayerRegistration.RegistrationStatus.REGISTERED)

    def test_end_loan_not_on_loan(self):
        """Test ending loan for player not on loan at the club."""
        with self.assertRaises(TransferError):
            PlayerTransferService.end_loan(
                player=self.player,
                loan_club=self.club1,
            )
