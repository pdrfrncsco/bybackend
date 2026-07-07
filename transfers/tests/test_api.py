"""
BOLAYETU — Transfer API Tests

Tests for transfer API endpoints.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date

from transfers.models import Transfer
from players.models import Player, PlayerRegistration
from clubs.models import Club
from competitions.models import Competition
from core.models import Tenant
from accounts.models import TenantMembership

User = get_user_model()


class TransferAPITestCase(TestCase):
    """Base test case for transfer API tests."""

    def setUp(self):
        self.client = APIClient()

        # Create tenant
        self.tenant = Tenant.objects.create(
            name="Test Federation",
            slug="test-federation"
        )

        # Create user and membership
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
        self.membership = TenantMembership.objects.create(
            user=self.user,
            tenant=self.tenant,
            role="admin"
        )

        # Create clubs
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

        # Create competition
        self.competition = Competition.objects.create(
            name="Test League",
            slug="test-league",
            tenant=self.tenant
        )

        # Create player
        self.player = Player.objects.create(
            first_name="João",
            last_name="Silva",
            slug="joao-silva",
            date_of_birth=date(1998, 5, 15),
            nationality="AO",
            primary_position="st"
        )

        # Create initial registration
        self.registration = PlayerRegistration.objects.create(
            player=self.player,
            club=self.from_club,
            tenant=self.tenant,
            shirt_number=9,
            joined_date=date(2024, 1, 1),
            status="registered"
        )

        self.client.force_authenticate(user=self.user)


class TransferListCreateViewTestCase(TransferAPITestCase):
    """Test GET/POST /api/v1/transfers/"""

    def test_list_transfers(self):
        """Test listing transfers."""
        # Create a transfer
        Transfer.objects.create(
            player=self.player,
            from_club=self.from_club,
            to_club=self.to_club,
            from_tenant=self.tenant,
            to_tenant=self.tenant,
            joined_date=date(2026, 7, 1),
            status=Transfer.TransferStatus.PENDING,
        )

        response = self.client.get('/api/v1/transfers/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 1)

    def test_create_transfer(self):
        """Test creating a transfer request."""
        data = {
            "player_id": str(self.player.id),
            "to_club_id": str(self.to_club.id),
            "from_club_id": str(self.from_club.id),
            "joined_date": "2026-07-01",
            "shirt_number": 10,
            "fee": "50000.00"
        }

        response = self.client.post('/api/v1/transfers/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['status'], 'pending')

    def test_create_free_agent_transfer(self):
        """Test creating a free agent transfer."""
        free_agent = Player.objects.create(
            first_name="Carlos",
            last_name="Santos",
            slug="carlos-santos",
            date_of_birth=date(2000, 3, 20),
            nationality="PT",
            primary_position="cb"
        )

        data = {
            "player_id": str(free_agent.id),
            "to_club_id": str(self.to_club.id),
            "joined_date": "2026-07-01",
            "shirt_number": 5
        }

        response = self.client.post('/api/v1/transfers/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Free agent transfers auto-complete
        self.assertEqual(response.data['data']['status'], 'completed')

    def test_filter_by_status(self):
        """Test filtering transfers by status."""
        Transfer.objects.create(
            player=self.player,
            from_club=self.from_club,
            to_club=self.to_club,
            from_tenant=self.tenant,
            to_tenant=self.tenant,
            joined_date=date(2026, 7, 1),
            status=Transfer.TransferStatus.PENDING,
        )

        response = self.client.get('/api/v1/transfers/?status=pending')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 1)


class TransferDetailViewTestCase(TransferAPITestCase):
    """Test GET /api/v1/transfers/{id}/"""

    def test_get_transfer_detail(self):
        """Test getting transfer details."""
        transfer = Transfer.objects.create(
            player=self.player,
            from_club=self.from_club,
            to_club=self.to_club,
            from_tenant=self.tenant,
            to_tenant=self.tenant,
            competition=self.competition,
            joined_date=date(2026, 7, 1),
            status=Transfer.TransferStatus.PENDING,
        )

        response = self.client.get(f'/api/v1/transfers/{transfer.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['status'], 'pending')
        self.assertIsNotNone(response.data['data']['player'])

    def test_get_nonexistent_transfer(self):
        """Test getting a transfer that doesn't exist."""
        response = self.client.get('/api/v1/transfers/00000000-0000-0000-0000-000000000000/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TransferApproveViewTestCase(TransferAPITestCase):
    """Test POST /api/v1/transfers/{id}/approve/"""

    def test_approve_transfer(self):
        """Test approving a transfer."""
        transfer = Transfer.objects.create(
            player=self.player,
            from_club=self.from_club,
            to_club=self.to_club,
            from_tenant=self.tenant,
            to_tenant=self.tenant,
            joined_date=date(2026, 7, 1),
            status=Transfer.TransferStatus.PENDING,
        )

        response = self.client.post(f'/api/v1/transfers/{transfer.id}/approve/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['status'], 'approved')


class TransferRejectViewTestCase(TransferAPITestCase):
    """Test POST /api/v1/transfers/{id}/reject/"""

    def test_reject_transfer(self):
        """Test rejecting a transfer."""
        transfer = Transfer.objects.create(
            player=self.player,
            from_club=self.from_club,
            to_club=self.to_club,
            from_tenant=self.tenant,
            to_tenant=self.tenant,
            joined_date=date(2026, 7, 1),
            status=Transfer.TransferStatus.PENDING,
        )

        data = {"rejection_reason": "Player not for sale."}
        response = self.client.post(f'/api/v1/transfers/{transfer.id}/reject/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['status'], 'rejected')
        self.assertEqual(response.data['data']['rejection_reason'], 'Player not for sale.')


class TransferCompleteViewTestCase(TransferAPITestCase):
    """Test POST /api/v1/transfers/{id}/complete/"""

    def test_complete_transfer(self):
        """Test completing an approved transfer."""
        transfer = Transfer.objects.create(
            player=self.player,
            from_club=self.from_club,
            to_club=self.to_club,
            from_tenant=self.tenant,
            to_tenant=self.tenant,
            competition=self.competition,
            joined_date=date(2026, 7, 1),
            status=Transfer.TransferStatus.APPROVED,
        )

        response = self.client.post(f'/api/v1/transfers/{transfer.id}/complete/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['status'], 'completed')

        # Verify new registration was created
        new_reg = PlayerRegistration.objects.filter(
            player=self.player,
            club=self.to_club,
            status="registered"
        ).first()
        self.assertIsNotNone(new_reg)
