from datetime import date, datetime, timezone

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import TenantMembership
from clubs.constants import ClubMemberRole
from clubs.models import Club, ClubMember
from competitions.models import Competition, Match
from core.models import Tenant
from players.models import Player, PlayerRegistration

User = get_user_model()


class ClubKpisTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.tenant = Tenant.objects.create(name="Test Org", slug="test-org")
        self.club = Club.objects.create(tenant=self.tenant, name="Test Club", slug="test-club", is_public=True)
        self.opponent = Club.objects.create(tenant=self.tenant, name="Opponents", slug="opponents", is_public=True)
        self.competition = Competition.objects.create(
            tenant=self.tenant,
            name="League 2026",
            competition_type="league",
            season="2026/27",
            status="active",
        )

        self.user = User.objects.create_user(email="admin@test.com", password="SecurePass123!", status="active")
        TenantMembership.objects.create(user=self.user, tenant=self.tenant, role="owner", is_active=True)

        self.player = Player.objects.create(
            first_name="Paulo",
            last_name="Silva",
            date_of_birth=date(2000, 1, 1),
            nationality="Angola",
            primary_position="fw",
        )
        PlayerRegistration.objects.create(
            player=self.player,
            club=self.club,
            competition=self.competition,
            tenant=self.tenant,
            shirt_number=9,
            joined_date=date(2026, 1, 1),
        )

        ClubMember.objects.create(
            club=self.club,
            user=self.user,
            full_name="Admin User",
            role=ClubMemberRole.MANAGER,
            is_active=True,
        )

        Match.objects.create(
            competition=self.competition,
            tenant=self.tenant,
            home_club=self.club,
            away_club=self.opponent,
            match_date=datetime(2026, 7, 1, 16, 0, tzinfo=timezone.utc),
            round_number=1,
            status=Match.MatchStatus.FINISHED,
            home_score=2,
            away_score=0,
        )

    def test_club_kpis_are_calculated_from_matches(self):
        response = self.client.get(f"/api/v1/clubs/public/{self.club.slug}/kpis/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        data = response.data["data"]
        self.assertEqual(data["squad_size"], 1)
        self.assertEqual(data["staff_count"], 1)
        self.assertEqual(data["total_matches"], 1)
        self.assertEqual(data["wins"], 1)
        self.assertEqual(data["draws"], 0)
        self.assertEqual(data["losses"], 0)
        self.assertEqual(data["goals_for"], 2)
        self.assertEqual(data["goals_against"], 0)
        self.assertEqual(data["clean_sheets"], 1)
        self.assertEqual(data["active_competitions"], 1)


class ClubDocumentsAndSponsorsAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.tenant = Tenant.objects.create(name="Test Org", slug="test-org")
        self.club = Club.objects.create(tenant=self.tenant, name="Test Club", slug="test-club", is_public=True)
        self.user = User.objects.create_user(email="admin@test.com", password="SecurePass123!", status="active")
        TenantMembership.objects.create(user=self.user, tenant=self.tenant, role="owner", is_active=True)
        self.client.force_authenticate(user=self.user)

    def _pdf(self, name="document.pdf"):
        return SimpleUploadedFile(name, b"%PDF-1.4 fake", content_type="application/pdf")

    def _png(self, name="logo.png"):
        return SimpleUploadedFile(name, b"\x89PNG\r\n\x1a\n", content_type="image/png")

    def test_upload_and_list_public_document(self):
        response = self.client.post(
            f"/api/v1/clubs/{self.club.slug}/documents/",
            {
                "title": "Licença 2026",
                "category": "license",
                "description": "Licença principal",
                "document": self._pdf(),
                "is_public": True,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertTrue(response.data["data"]["asset_url"])

        public_response = self.client.get(f"/api/v1/clubs/public/{self.club.slug}/documents/")
        self.assertEqual(public_response.status_code, status.HTTP_200_OK)
        self.assertEqual(public_response.data["data"]["count"], 1)
        self.assertEqual(public_response.data["data"]["results"][0]["title"], "Licença 2026")

    def test_create_and_list_public_sponsor(self):
        response = self.client.post(
            f"/api/v1/clubs/{self.club.slug}/sponsors/",
            {
                "name": "Banco Teste",
                "sponsor_type": "partner",
                "description": "Patrocinador principal",
                "website": "https://example.com",
                "logo": self._png(),
                "is_active": True,
                "sort_order": 1,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertTrue(response.data["data"]["logo_url"])

        public_response = self.client.get(f"/api/v1/clubs/public/{self.club.slug}/sponsors/")
        self.assertEqual(public_response.status_code, status.HTTP_200_OK)
        self.assertEqual(public_response.data["data"]["count"], 1)
        self.assertEqual(public_response.data["data"]["results"][0]["name"], "Banco Teste")
