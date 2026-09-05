from datetime import date

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import TenantMembership
from clubs.constants import ClubMemberRole
from clubs.models import Club, ClubMember
from competitions.constants import CompetitionStatus
from competitions.models import Competition
from core.models import Tenant
from players.models import Player, PlayerRegistration, PlayerRegistrationRequest

User = get_user_model()


class PlayerRegistrationRequestAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.tenant = Tenant.objects.create(name="Test Org", slug="test-org", status=Tenant.TenantStatus.ACTIVE)
        self.club = Club.objects.create(tenant=self.tenant, name="Test Club", slug="test-club", is_public=True)
        self.other_club = Club.objects.create(tenant=self.tenant, name="Other Club", slug="other-club", is_public=True)

        self.player_user = User.objects.create_user(
            email="player@test.com",
            password="SecurePass123!",
            status="active",
        )
        self.club_admin = User.objects.create_user(
            email="clubadmin@test.com",
            password="SecurePass123!",
            status="active",
        )

        self.player = Player.objects.create(
            user=self.player_user,
            first_name="Joao",
            last_name="Silva",
            slug="joao-silva",
            date_of_birth=date(2000, 1, 1),
            nationality="AO",
            primary_position="st",
            status="active",
        )

        TenantMembership.objects.create(user=self.club_admin, tenant=self.tenant, role="owner", is_active=True)
        ClubMember.objects.create(
            club=self.club,
            user=self.club_admin,
            full_name="Club Admin",
            role=ClubMemberRole.MANAGER,
            is_active=True,
        )

    def test_player_submits_registration_request(self):
        self.client.force_authenticate(user=self.player_user)
        response = self.client.post(
            "/api/v1/players/me/registration-requests/",
            {
                "club_id": str(self.club.id),
                "joined_date": "2026-07-01",
                "shirt_number": 9,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertTrue(
            PlayerRegistrationRequest.objects.filter(
                player=self.player,
                club=self.club,
                status=PlayerRegistrationRequest.Status.PENDING,
            ).exists()
        )

    def test_player_cannot_request_unregistered_competition(self):
        competition = Competition.objects.create(
            tenant=self.tenant,
            name="Test League",
            season="2026",
            status=CompetitionStatus.ACTIVE,
        )

        self.client.force_authenticate(user=self.player_user)
        response = self.client.post(
            "/api/v1/players/me/registration-requests/",
            {
                "club_id": str(self.club.id),
                "joined_date": "2026-07-01",
                "competition_id": str(competition.id),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(
            PlayerRegistrationRequest.objects.filter(
                player=self.player,
                club=self.club,
            ).exists()
        )

    def test_player_cannot_request_competition_from_another_tenant(self):
        other_tenant = Tenant.objects.create(
            name="Other Org", slug="other-org", status=Tenant.TenantStatus.ACTIVE
        )
        foreign_competition = Competition.objects.create(
            tenant=other_tenant,
            name="Foreign League",
            season="2026",
            status=CompetitionStatus.ACTIVE,
        )

        self.client.force_authenticate(user=self.player_user)
        response = self.client.post(
            "/api/v1/players/me/registration-requests/",
            {
                "club_id": str(self.club.id),
                "joined_date": "2026-07-01",
                "competition_id": str(foreign_competition.id),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(
            PlayerRegistrationRequest.objects.filter(player=self.player, club=self.club).exists()
        )

    def test_club_cannot_invite_player_to_competition_from_another_tenant(self):
        other_tenant = Tenant.objects.create(
            name="Other Org", slug="other-org", status=Tenant.TenantStatus.ACTIVE
        )
        foreign_competition = Competition.objects.create(
            tenant=other_tenant,
            name="Foreign League",
            season="2026",
            status=CompetitionStatus.ACTIVE,
        )

        self.client.force_authenticate(user=self.club_admin)
        response = self.client.post(
            f"/api/v1/players/{self.player.slug}/register/",
            {
                "club_id": str(self.club.id),
                "joined_date": "2026-07-01",
                "competition_id": str(foreign_competition.id),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(
            PlayerRegistrationRequest.objects.filter(
                player=self.player,
                club=self.club,
                status=PlayerRegistrationRequest.Status.INVITED,
            ).exists()
        )

    def test_pending_request_constraint_covers_null_competition(self):
        PlayerRegistrationRequest.objects.create(
            player=self.player,
            club=self.club,
            tenant=self.tenant,
            submitted_by=self.player_user,
            joined_date=date(2026, 7, 1),
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PlayerRegistrationRequest.objects.create(
                    player=self.player,
                    club=self.club,
                    tenant=self.tenant,
                    submitted_by=self.player_user,
                    joined_date=date(2026, 7, 2),
                )

    def test_review_is_idempotent_after_a_decision(self):
        request_obj = PlayerRegistrationRequest.objects.create(
            player=self.player,
            club=self.club,
            tenant=self.tenant,
            submitted_by=self.player_user,
            joined_date=date(2026, 7, 1),
        )

        self.client.force_authenticate(user=self.club_admin)
        first_response = self.client.patch(
            f"/api/v1/clubs/me/player-registration-requests/{request_obj.id}/",
            {"approve": True},
            format="json",
        )
        second_response = self.client.patch(
            f"/api/v1/clubs/me/player-registration-requests/{request_obj.id}/",
            {"approve": False},
            format="json",
        )

        self.assertEqual(first_response.status_code, status.HTTP_200_OK)
        self.assertEqual(second_response.status_code, status.HTTP_409_CONFLICT)
        request_obj.refresh_from_db()
        self.assertEqual(request_obj.status, PlayerRegistrationRequest.Status.APPROVED)

    def test_player_lists_own_registration_requests(self):
        PlayerRegistrationRequest.objects.create(
            player=self.player,
            club=self.club,
            tenant=self.tenant,
            submitted_by=self.player_user,
            joined_date=date(2026, 7, 1),
        )

        self.client.force_authenticate(user=self.player_user)
        response = self.client.get("/api/v1/players/me/registration-requests/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]), 1)

    def test_club_admin_lists_registration_requests(self):
        PlayerRegistrationRequest.objects.create(
            player=self.player,
            club=self.club,
            tenant=self.tenant,
            submitted_by=self.player_user,
            joined_date=date(2026, 7, 1),
        )

        self.client.force_authenticate(user=self.club_admin)
        response = self.client.get("/api/v1/clubs/me/player-registration-requests/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]), 1)

    def test_club_admin_approves_request_and_player_accepts_registration(self):
        request_obj = PlayerRegistrationRequest.objects.create(
            player=self.player,
            club=self.club,
            tenant=self.tenant,
            submitted_by=self.player_user,
            joined_date=date(2026, 7, 1),
            shirt_number=9,
            status=PlayerRegistrationRequest.Status.PENDING,
        )

        self.client.force_authenticate(user=self.club_admin)
        response = self.client.patch(
            f"/api/v1/clubs/me/player-registration-requests/{request_obj.id}/",
            {"approve": True, "review_notes": "Aprovado"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        request_obj.refresh_from_db()
        self.assertEqual(request_obj.status, PlayerRegistrationRequest.Status.APPROVED)

        self.client.force_authenticate(user=self.player_user)
        response = self.client.post(
            f"/api/v1/players/me/registration-requests/{request_obj.id}/accept/",
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        request_obj.refresh_from_db()
        self.assertIsNotNone(request_obj.registration)
        self.assertTrue(
            PlayerRegistration.objects.filter(player=self.player, club=self.club, status="registered").exists()
        )

    def test_club_admin_rejects_request(self):
        request_obj = PlayerRegistrationRequest.objects.create(
            player=self.player,
            club=self.club,
            tenant=self.tenant,
            submitted_by=self.player_user,
            joined_date=date(2026, 7, 1),
            status=PlayerRegistrationRequest.Status.PENDING,
        )

        self.client.force_authenticate(user=self.club_admin)
        response = self.client.patch(
            f"/api/v1/clubs/me/player-registration-requests/{request_obj.id}/",
            {"approve": False, "review_notes": "Documentação incompleta"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        request_obj.refresh_from_db()
        self.assertEqual(request_obj.status, PlayerRegistrationRequest.Status.REJECTED)
        self.assertIsNone(request_obj.registration)
        self.assertFalse(PlayerRegistration.objects.filter(player=self.player, club=self.club).exists())
