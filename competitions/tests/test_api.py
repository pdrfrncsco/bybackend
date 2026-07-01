from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date, datetime

from core.models import Tenant
from accounts.models import TenantMembership
from clubs.models import Club
from competitions.models import Competition, CompetitionRegistration, Match, Standing
from competitions.services import CompetitionService
from competitions.services.competition_registration_service import CompetitionRegistrationService
from competitions.services.match_service import MatchService

User = get_user_model()


class CompetitionAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create user & tenant
        self.user = User.objects.create_user(
            email="admin@bolayetu.com",
            password="SecurePass123!",
            status="active"
        )
        self.tenant = Tenant.objects.create(name="Angolan Football Association", slug="faf")

        # Make user organization admin/owner
        TenantMembership.objects.create(
            user=self.user,
            tenant=self.tenant,
            role="owner",
            is_active=True,
        )

        # Authenticate
        self.client.force_authenticate(user=self.user)

        # Create competition
        self.competition = CompetitionService.create_competition(
            tenant=self.tenant,
            name="Girabola",
            competition_type="league",
            season="2025/26",
        )

        # Create clubs
        self.club1 = Club.objects.create(name="Petro de Luanda", slug="petro-luanda", tenant=self.tenant, city="Luanda")
        self.club2 = Club.objects.create(name="1º de Agosto", slug="primeiro-agosto", tenant=self.tenant, city="Luanda")

    def test_register_club_api(self):
        """Test registering a club via POST API."""
        url = f"/api/v1/competitions/{self.competition.id}/register-club/"
        payload = {"club": str(self.club1.id)}
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["success"], True)
        self.assertTrue(CompetitionRegistration.objects.filter(competition=self.competition, club=self.club1).exists())

    def test_generate_schedule_api(self):
        """Test generating berger schedule calendar via POST API."""
        # First register clubs
        CompetitionRegistrationService.register_club(tenant=self.tenant, competition=self.competition, club=self.club1)
        CompetitionRegistrationService.register_club(tenant=self.tenant, competition=self.competition, club=self.club2)

        url = f"/api/v1/competitions/{self.competition.id}/generate-schedule/"
        payload = {
            "start_date": "2026-08-01",
            "rounds_interval_days": 7,
            "double_round": True
        }
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["success"], True)
        self.assertEqual(Match.objects.filter(competition=self.competition).count(), 2)  # 2 teams: 1 round * 2 legs = 2 matches

    def test_list_matches_api(self):
        """Test public GET list matches endpoint."""
        # Create a mock match
        match = Match.objects.create(
            competition=self.competition,
            tenant=self.tenant,
            home_club=self.club1,
            away_club=self.club2,
            match_date=datetime(2026, 8, 1, 16, 0),
            round_number=1,
            status=Match.MatchStatus.SCHEDULED,
        )

        # AllowAny - unauthenticate for this test
        self.client.force_authenticate(user=None)
        
        url = f"/api/v1/competitions/{self.competition.id}/matches/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["success"], True)
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["data"][0]["id"], str(match.id))

    def test_update_match_score_api(self):
        """Test PATCH update match score and standings recalculation."""
        # Register clubs
        CompetitionRegistrationService.register_club(tenant=self.tenant, competition=self.competition, club=self.club1)
        CompetitionRegistrationService.register_club(tenant=self.tenant, competition=self.competition, club=self.club2)

        # Create a match
        match = Match.objects.create(
            competition=self.competition,
            tenant=self.tenant,
            home_club=self.club1,
            away_club=self.club2,
            match_date=datetime(2026, 8, 1, 16, 0),
            round_number=1,
            status=Match.MatchStatus.SCHEDULED,
        )

        url = f"/api/v1/competitions/matches/{match.id}/"
        payload = {
            "home_score": 3,
            "away_score": 2,
            "status": "finished"
        }
        response = self.client.patch(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["success"], True)
        
        # Check standing of club1
        standing = Standing.objects.get(competition=self.competition, club=self.club1)
        self.assertEqual(standing.points, 3)
        self.assertEqual(standing.goals_for, 3)
        self.assertEqual(standing.goals_against, 2)

    def test_get_standings_api(self):
        """Test public GET standings endpoint."""
        # Register and setup initial standing
        CompetitionRegistrationService.register_club(tenant=self.tenant, competition=self.competition, club=self.club1)

        # AllowAny - unauthenticate for this test
        self.client.force_authenticate(user=None)

        url = f"/api/v1/competitions/{self.competition.id}/standings/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["success"], True)
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["data"][0]["club_name"], "Petro de Luanda")
