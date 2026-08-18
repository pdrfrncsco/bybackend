from datetime import date, datetime, timezone

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import TenantMembership
from clubs.models import Club
from competitions.models import Competition, CompetitionRegistration, Match, Standing
from competitions.services import CompetitionService
from competitions.services.competition_registration_service import CompetitionRegistrationService
from competitions.services.match_service import MatchService
from core.models import Tenant

User = get_user_model()


class CompetitionAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create user & tenant
        self.user = User.objects.create_user(email="admin@bolayetu.com", password="SecurePass123!", status="active")
        self.tenant = Tenant.objects.create(
            name="Angolan Football Association",
            slug="faf",
            subdomain="faf",
        )

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
        payload = {"start_date": "2026-08-01", "rounds_interval_days": 7, "double_round": True}
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["success"], True)
        self.assertEqual(
            Match.objects.filter(competition=self.competition).count(), 2
        )  # 2 teams: 1 round * 2 legs = 2 matches

    def test_generate_schedule_api_uses_knockout_draw_for_cup(self):
        """Cup competitions should branch to knockout draw generation."""
        cup = CompetitionService.create_competition(
            tenant=self.tenant,
            name="Taça Nacional",
            competition_type="cup",
            season="2026/27",
        )
        for club in [self.club1, self.club2]:
            CompetitionRegistrationService.register_club(
                tenant=self.tenant,
                competition=cup,
                club=club,
            )

        response = self.client.post(
            f"/api/v1/competitions/{cup.id}/generate-schedule/",
            {"start_date": "2026-08-01", "seed": "fixed-seed"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["success"], True)
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["data"][0]["phase"], "knockout")
        self.assertEqual(response.data["data"][0]["round_name"], "Final")

    def test_create_competition_with_config_api(self):
        """POST /competitions/ should persist config in the created competition."""
        url = "/api/v1/competitions/"
        payload = {
            "name": "Taça Nacional",
            "competition_type": "cup",
            "season": "2026/27",
            "status": "draft",
            "config": {
                "pointsWin": 3,
                "pointsDraw": 1,
                "pointsLoss": 0,
            },
        }

        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["success"], True)
        self.assertEqual(response.data["data"]["config"]["pointsWin"], 3)

        competition = Competition.objects.get(name="Taça Nacional")
        self.assertEqual(competition.config["pointsDraw"], 1)

    def test_get_and_patch_competition_config_api(self):
        """Competition config endpoint should retrieve and update config independently."""
        url = f"/api/v1/competitions/{self.competition.id}/config/"

        get_response = self.client.get(url)
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_response.data["success"], True)
        self.assertEqual(get_response.data["data"]["config"], {})

        patch_payload = {
            "config": {
                "pointsWin": 4,
                "pointsDraw": 2,
                "pointsLoss": 0,
                "tiebreakers": ["goalDifference", "goalsFor"],
            }
        }
        patch_response = self.client.patch(url, patch_payload, format="json")

        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_response.data["success"], True)
        self.assertEqual(patch_response.data["data"]["config"]["pointsWin"], 4)

        self.competition.refresh_from_db()
        self.assertEqual(self.competition.config["tiebreakers"], ["goalDifference", "goalsFor"])

    def test_list_matches_api(self):
        """Test public GET list matches endpoint."""
        # Create a mock match
        match = Match.objects.create(
            competition=self.competition,
            tenant=self.tenant,
            home_club=self.club1,
            away_club=self.club2,
            match_date=datetime(2026, 8, 1, 16, 0, tzinfo=timezone.utc),
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

    def test_create_match_api(self):
        """Test creating a manual match through the competition matches endpoint."""
        CompetitionRegistrationService.register_club(tenant=self.tenant, competition=self.competition, club=self.club1)
        CompetitionRegistrationService.register_club(tenant=self.tenant, competition=self.competition, club=self.club2)

        url = f"/api/v1/competitions/{self.competition.id}/matches/"
        payload = {
            "home_club": str(self.club1.id),
            "away_club": str(self.club2.id),
            "match_date": "2026-08-01T16:00:00Z",
            "round_number": 2,
            "round_name": "Jornada 2",
            "venue": "Estádio 11 de Novembro",
        }
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["success"], True)
        self.assertEqual(str(response.data["data"]["home_club"]), str(self.club1.id))
        self.assertEqual(str(response.data["data"]["away_club"]), str(self.club2.id))
        self.assertEqual(Match.objects.filter(competition=self.competition).count(), 1)

    def test_create_match_api_rejects_league_context_fields(self):
        """League matches should reject phase/group fields to avoid invalid context data."""
        CompetitionRegistrationService.register_club(tenant=self.tenant, competition=self.competition, club=self.club1)
        CompetitionRegistrationService.register_club(tenant=self.tenant, competition=self.competition, club=self.club2)

        url = f"/api/v1/competitions/{self.competition.id}/matches/"
        payload = {
            "home_club": str(self.club1.id),
            "away_club": str(self.club2.id),
            "match_date": "2026-08-01T16:00:00Z",
            "round_number": 2,
            "phase": "knockout",
            "group_id": "A",
        }
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["success"], False)
        self.assertIn("phase or group", response.data["message"])

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
            match_date=datetime(2026, 8, 1, 16, 0, tzinfo=timezone.utc),
            round_number=1,
            status=Match.MatchStatus.SCHEDULED,
        )

        url = f"/api/v1/competitions/matches/{match.id}/"
        payload = {"home_score": 3, "away_score": 2, "status": "finished"}
        response = self.client.patch(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["success"], True)

        # Check standing of club1
        standing = Standing.objects.get(competition=self.competition, club=self.club1)
        self.assertEqual(standing.points, 3)
        self.assertEqual(standing.goals_for, 3)
        self.assertEqual(standing.goals_against, 2)

    def test_get_match_detail_api_exposes_canonical_contract(self):
        """Detail endpoint should expose a canonical match contract and compatibility aliases."""
        match = Match.objects.create(
            competition=self.competition,
            tenant=self.tenant,
            home_club=self.club1,
            away_club=self.club2,
            match_date=datetime(2026, 8, 1, 16, 0, tzinfo=timezone.utc),
            round_number=2,
            round_name="Jornada 2",
            status=Match.MatchStatus.LIVE,
            home_score=1,
            away_score=0,
            venue="Arena",
        )

        self.client.force_authenticate(user=None)
        response = self.client.get(f"/api/v1/competitions/{self.competition.id}/matches/{match.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["success"], True)
        payload = response.data["data"]
        self.assertEqual(payload["id"], str(match.id))
        self.assertEqual(payload["competition_id"], str(self.competition.id))
        self.assertEqual(payload["home_team_id"], str(self.club1.id))
        self.assertEqual(payload["away_team_id"], str(self.club2.id))
        self.assertEqual(payload["home_team_name"], "Petro de Luanda")
        self.assertEqual(payload["away_team_name"], "1º de Agosto")
        self.assertEqual(payload["status"], "live")
        self.assertEqual(payload["status_label"], "Em Curso")
        self.assertEqual(payload["scheduled_at"], payload["match_date"])

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

    def test_get_standings_api_filters_by_context(self):
        """Standings endpoint should support group and phase filters."""
        other_club = Club.objects.create(
            name="Interclube",
            slug="interclube",
            tenant=self.tenant,
            city="Luanda",
        )
        CompetitionRegistrationService.register_club(
            tenant=self.tenant,
            competition=self.competition,
            club=other_club,
        )

        Standing.objects.create(
            competition=self.competition,
            tenant=self.tenant,
            club=self.club1,
            group_id="A",
            phase="group_stage",
            points=3,
            position=1,
        )
        Standing.objects.create(
            competition=self.competition,
            tenant=self.tenant,
            club=other_club,
            group_id="B",
            phase="group_stage",
            points=1,
            position=1,
        )

        self.client.force_authenticate(user=None)
        response = self.client.get(
            f"/api/v1/competitions/{self.competition.id}/standings/?groupId=A&phase=group_stage"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["success"], True)
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["data"][0]["club_name"], "Petro de Luanda")

    def test_draw_bracket_and_rounds_api(self):
        """Draw should generate bracket data and rounds endpoints should expose it."""
        cup = CompetitionService.create_competition(
            tenant=self.tenant,
            name="Taça de Luanda",
            competition_type="cup",
            season="2026/27",
        )
        club3 = Club.objects.create(name="Sagrada Esperança", slug="sagrada-esperanca-api", tenant=self.tenant, city="Dundo")
        club4 = Club.objects.create(name="Wiliete de Benguela", slug="wiliete-benguela-api", tenant=self.tenant, city="Benguela")

        for club in [self.club1, self.club2, club3, club4]:
            CompetitionRegistrationService.register_club(
                tenant=self.tenant,
                competition=cup,
                club=club,
            )

        draw_response = self.client.post(
            f"/api/v1/competitions/{cup.id}/draw/",
            {"start_date": "2026-08-01", "seed": "fixed-seed"},
            format="json",
        )
        self.assertEqual(draw_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(draw_response.data["success"], True)
        self.assertEqual(len(draw_response.data["data"]["matches"]), 2)
        self.assertEqual(len(draw_response.data["data"]["bracket"]["rounds"]), 1)

        bracket_response = self.client.get(f"/api/v1/competitions/{cup.id}/bracket/")
        self.assertEqual(bracket_response.status_code, status.HTTP_200_OK)
        self.assertEqual(bracket_response.data["success"], True)
        self.assertEqual(len(bracket_response.data["data"]["rounds"]), 1)
        self.assertEqual(bracket_response.data["data"]["rounds"][0]["round_name"], "Semi-finals")

        rounds_response = self.client.get(f"/api/v1/competitions/{cup.id}/rounds/")
        self.assertEqual(rounds_response.status_code, status.HTTP_200_OK)
        self.assertEqual(rounds_response.data["success"], True)
        self.assertEqual(len(rounds_response.data["data"]), 1)
        self.assertEqual(rounds_response.data["data"][0]["matches_count"], 2)

    def test_draw_bracket_exposes_byes_explicitly(self):
        """Draw bracket should include explicit byes for incomplete knockout slots."""
        cup = CompetitionService.create_competition(
            tenant=self.tenant,
            name="Taça com Byes",
            competition_type="cup",
            season="2026/27",
        )
        clubs = [
            self.club1,
            self.club2,
            Club.objects.create(name="Sagrada Esperança", slug="sagrada-esperanca-bye", tenant=self.tenant, city="Dundo"),
            Club.objects.create(name="Wiliete de Benguela", slug="wiliete-benguela-bye", tenant=self.tenant, city="Benguela"),
            Club.objects.create(name="Interclube", slug="interclube-bye", tenant=self.tenant, city="Luanda"),
        ]
        for club in clubs:
            CompetitionRegistrationService.register_club(
                tenant=self.tenant,
                competition=cup,
                club=club,
            )

        self.client.force_authenticate(user=self.user)
        self.client.post(
            f"/api/v1/competitions/{cup.id}/draw/",
            {"start_date": "2026-08-01", "seed": "fixed-seed"},
            format="json",
        )

        bracket_response = self.client.get(f"/api/v1/competitions/{cup.id}/bracket/")
        self.assertEqual(bracket_response.status_code, status.HTTP_200_OK)
        first_round = bracket_response.data["data"]["rounds"][0]
        self.assertEqual(first_round["round_number"], 1)
        self.assertEqual(len(first_round["byes"]), 3)
        self.assertTrue(all("club" in item for item in first_round["byes"]))

    @override_settings(ALLOWED_HOSTS=["testserver", ".bolayetu.com"])
    def test_list_competitions_filters_by_subdomain_tenant(self):
        """Public competition list should use request.tenant when subdomain is present."""
        other_tenant = Tenant.objects.create(
            name="Luanda League",
            slug="luanda",
            subdomain="luanda",
        )
        CompetitionService.create_competition(
            tenant=other_tenant,
            name="Liga Luanda",
            competition_type="league",
            season="2025/26",
        )

        self.client.force_authenticate(user=None)

        response = self.client.get(
            "/api/v1/competitions/",
            HTTP_HOST="faf.bolayetu.com",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["success"], True)
        self.assertEqual(len(response.data["data"]["results"]), 1)
        self.assertEqual(response.data["data"]["results"][0]["id"], str(self.competition.id))

    @override_settings(ALLOWED_HOSTS=["testserver", ".bolayetu.com"])
    def test_competition_detail_returns_404_for_other_subdomain_tenant(self):
        """Public detail should not expose a competition from another tenant on subdomain routes."""
        other_tenant = Tenant.objects.create(
            name="Luanda League",
            slug="luanda",
            subdomain="luanda",
        )
        other_competition = CompetitionService.create_competition(
            tenant=other_tenant,
            name="Liga Luanda",
            competition_type="league",
            season="2025/26",
        )

        self.client.force_authenticate(user=None)

        response = self.client.get(
            f"/api/v1/competitions/{other_competition.id}/",
            HTTP_HOST="faf.bolayetu.com",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
