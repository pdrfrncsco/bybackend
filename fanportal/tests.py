from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from core.models import Tenant
from usuarios.models import User
from clubs.models import Club
from torneios.models import Tournament, TournamentGroup
from partidas.models import Match
from classificacoes.models import Standing
from matchengine.models import MatchEvent, MatchStats


class FanPortalTournamentOverviewTests(APITestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Org", slug="org")
        self.user = User.objects.create_user(
            username="fan",
            password="password",
            tenant=self.tenant,
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

        self.club1 = Club.objects.create(tenant=self.tenant, name="Clube A")
        self.club2 = Club.objects.create(tenant=self.tenant, name="Clube B")

        self.tournament = Tournament.objects.create(
            tenant=self.tenant,
            name="Liga Teste",
            season="2024",
            start_date=timezone.now().date(),
            status="active",
            type="League",
        )
        self.tournament.clubs.add(self.club1, self.club2)

        self.match = Match.objects.create(
            tenant=self.tenant,
            tournament=self.tournament,
            home_team=self.club1,
            away_team=self.club2,
            date=timezone.now(),
            status="finished",
            home_score=2,
            away_score=1,
        )

        MatchEvent.objects.create(
            tenant=self.tenant,
            match=self.match,
            team=self.club1,
            type="goal",
            minute=10,
        )

        MatchStats.objects.create(
            tenant=self.tenant,
            match=self.match,
            home_possession=60,
            away_possession=40,
            home_shots=5,
            away_shots=3,
            home_corners=2,
            away_corners=1,
            home_fouls=4,
            away_fouls=6,
        )

        Standing.objects.create(
            tenant=self.tenant,
            tournament=self.tournament,
            group=None,
            club=self.club1,
            played=1,
            wins=1,
            draws=0,
            losses=0,
            goals_for=2,
            goals_against=1,
            points=3,
        )

        Standing.objects.create(
            tenant=self.tenant,
            tournament=self.tournament,
            group=None,
            club=self.club2,
            played=1,
            wins=0,
            draws=0,
            losses=1,
            goals_for=1,
            goals_against=2,
            points=0,
        )

    def test_overview_returns_matches_standings_and_stats(self):
        url = reverse(
            "fanportal-tournament-overview", kwargs={"tournament_id": self.tournament.id}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertIn("tournament", data)
        self.assertIn("matches", data)
        self.assertIn("participants", data)

        matches = data["matches"]
        self.assertEqual(len(matches), 1)
        match_payload = matches[0]
        self.assertEqual(match_payload["homeTeamName"], "Clube A")
        self.assertEqual(match_payload["awayTeamName"], "Clube B")
        self.assertIn("events", match_payload)
        self.assertIn("stats", match_payload)

        tournament_payload = data["tournament"]
        table = tournament_payload.get("table") or []
        self.assertEqual(len(table), 2)

    def test_live_match_scores_follow_events(self):
        live_match = Match.objects.create(
            tenant=self.tenant,
            tournament=self.tournament,
            home_team=self.club1,
            away_team=self.club2,
            date=timezone.now(),
            status="live",
            home_score=None,
            away_score=None,
        )

        MatchEvent.objects.create(
            tenant=self.tenant,
            match=live_match,
            team=self.club1,
            type="goal",
            minute=5,
        )
        MatchEvent.objects.create(
            tenant=self.tenant,
            match=live_match,
            team=self.club2,
            type="goal",
            minute=20,
            is_own_goal=True,
        )

        url = reverse(
            "fanportal-tournament-overview", kwargs={"tournament_id": self.tournament.id}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        matches = data["matches"]
        self.assertEqual(len(matches), 2)

        payload = next(m for m in matches if m["id"] == str(live_match.id))
        self.assertEqual(payload["homeScore"], 2)
        self.assertEqual(payload["awayScore"], 0)


class FanPortalGroupsOverviewTests(APITestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Org G", slug="org-g")
        self.user = User.objects.create_user(
            username="fan-g",
            password="password",
            tenant=self.tenant,
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

        self.club1 = Club.objects.create(tenant=self.tenant, name="Grupo Clube A")
        self.club2 = Club.objects.create(tenant=self.tenant, name="Grupo Clube B")

        self.tournament = Tournament.objects.create(
            tenant=self.tenant,
            name="Fase de Grupos",
            season="2024",
            start_date=timezone.now().date(),
            status="active",
            type="Groups",
        )
        self.tournament.clubs.add(self.club1, self.club2)

        self.group = TournamentGroup.objects.create(
            tenant=self.tenant, tournament=self.tournament, name="A"
        )
        self.group.clubs.add(self.club1, self.club2)

        Standing.objects.create(
            tenant=self.tenant,
            tournament=self.tournament,
            group=self.group,
            club=self.club1,
            played=1,
            wins=1,
            draws=0,
            losses=0,
            goals_for=3,
            goals_against=0,
            points=3,
        )

    def test_overview_includes_groups_payload(self):
        url = reverse(
            "fanportal-tournament-overview", kwargs={"tournament_id": self.tournament.id}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        tournament_payload = data["tournament"]
        groups = tournament_payload.get("groups") or []
        self.assertEqual(len(groups), 1)
        first_group = groups[0]
        self.assertEqual(first_group["name"], "A")
        self.assertTrue(first_group["table"])
