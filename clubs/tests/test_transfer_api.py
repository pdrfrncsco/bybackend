"""
BOLAYETU — Transfer API Tests

Tests for Transfer REST endpoints.
"""

from rest_framework.test import APITestCase
from rest_framework import status
from datetime import date, timedelta
from decimal import Decimal

from core.models import Tenant
from clubs.models import Club, Transfer
from players.models import Player
from accounts.models import User


class TransferAPITestCase(APITestCase):
    """Test Transfer API endpoints."""

    def setUp(self):
        """Set up test data."""
        # Create tenant and user
        self.tenant = Tenant.objects.create(name="Test FC", slug="test-fc")
        self.user = User.objects.create_user(
            email="admin@test.com",
            password="password123",
            is_staff=True,
        )
        self.user.tenant = self.tenant
        self.user.save()
        self.client.force_authenticate(user=self.user)

        # Create clubs
        self.home_club = Club.objects.create(
            tenant=self.tenant,
            name="Home FC",
            slug="home-fc",
            status="active",
        )
        self.away_club = Club.objects.create(
            tenant=self.tenant,
            name="Away FC",
            slug="away-fc",
            status="active",
        )

        # Create player
        self.player = Player.objects.create(
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1995, 1, 1),
            primary_position=Player.Position.CM,
        )

    def test_create_free_agent_transfer(self):
        """Test creating a free agent transfer."""
        data = {
            "player_id": str(self.player.id),
            "to_club_id": str(self.home_club.id),
            "transfer_type": "free_agent",
            "transfer_date": str(date.today()),
        }

        response = self.client.post("/api/v1/clubs/transfers/", data, format="json")

        if response.status_code != status.HTTP_201_CREATED:
            print("ERROR RESPONSE:", response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)

    def test_create_permanent_transfer(self):
        """Test creating a permanent transfer."""
        data = {
            "player_id": str(self.player.id),
            "to_club_id": str(self.away_club.id),
            "from_club_id": str(self.home_club.id),
            "transfer_type": "permanent",
            "transfer_date": str(date.today()),
            "fee": "1000000.00",
        }

        response = self.client.post("/api/v1/clubs/transfers/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_loan_transfer(self):
        """Test creating a loan transfer."""
        loan_end = date.today() + timedelta(days=180)
        data = {
            "player_id": str(self.player.id),
            "to_club_id": str(self.away_club.id),
            "from_club_id": str(self.home_club.id),
            "transfer_type": "loan",
            "transfer_date": str(date.today()),
            "loan_end_date": str(loan_end),
        }

        response = self.client.post("/api/v1/clubs/transfers/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_list_transfers(self):
        """Test listing transfers."""
        response = self.client.get("/api/v1/clubs/transfers/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Response is wrapped in success wrapper
        self.assertIn("data", response.data)

    def test_get_transfer(self):
        """Test getting a single transfer."""
        # Create a transfer
        transfer = Transfer.objects.create(
            tenant=self.tenant,
            player=self.player,
            to_club=self.home_club,
            transfer_type=Transfer.TransferType.FREE_AGENT,
            transfer_date=date.today(),
            status=Transfer.TransferStatus.COMPLETED,
        )

        response = self.client.get(f"/api/v1/clubs/transfers/{transfer.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data["id"]), str(transfer.id))
