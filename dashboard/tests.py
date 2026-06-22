from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from core.models import Tenant
from clubes.models import Club
from jogadores.models import Player, PlayerHistory
from torneios.models import Tournament
from partidas.models import Match
from .views import DashboardOverviewView


User = get_user_model()


class DashboardOverviewViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

        self.tenant1 = Tenant.objects.create(name="Tenant 1", slug="tenant-1")
        self.tenant2 = Tenant.objects.create(name="Tenant 2", slug="tenant-2")

        self.user1 = User.objects.create_user(
            username="user1", email="user1@example.com", password="testpass", tenant=self.tenant1
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@example.com", password="testpass", tenant=self.tenant2
        )

        self.user1.role = "manager"
        self.user1.save()
        self.user2.role = "manager"
        self.user2.save()

        now = timezone.now()

        self.club_t1 = Club.objects.create(tenant=self.tenant1, name="Clube Tenant 1")
        self.club_t2 = Club.objects.create(tenant=self.tenant2, name="Clube Tenant 2")

        self.player_t1 = Player.objects.create(
            tenant=self.tenant1,
            name="Jogador T1",
            club=self.club_t1,
            joined_date=now.date(),
        )
        self.player_t2 = Player.objects.create(
            tenant=self.tenant2,
            name="Jogador T2",
            club=self.club_t2,
            joined_date=now.date(),
        )

        self.tournament_t1 = Tournament.objects.create(
            tenant=self.tenant1,
            name="Torneio T1",
            season="2024/2025",
            start_date=now.date(),
            status="active",
        )
        self.tournament_t2 = Tournament.objects.create(
            tenant=self.tenant2,
            name="Torneio T2",
            season="2024/2025",
            start_date=now.date(),
            status="active",
        )

        Match.objects.create(
            tenant=self.tenant1,
            tournament=self.tournament_t1,
            home_team=self.club_t1,
            away_team=self.club_t1,
            home_score=1,
            away_score=0,
            date=now,
            status="finished",
        )
        Match.objects.create(
            tenant=self.tenant2,
            tournament=self.tournament_t2,
            home_team=self.club_t2,
            away_team=self.club_t2,
            home_score=2,
            away_score=1,
            date=now,
            status="finished",
        )

    def test_overview_is_filtered_by_user_tenant(self):
        request = self.factory.get("/api/dashboard/overview/")
        force_authenticate(request, user=self.user1)

        response = DashboardOverviewView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        kpis = response.data["kpis"]

        self.assertEqual(kpis["total_clubs"], 1)
        self.assertEqual(kpis["total_players"], 1)
        self.assertEqual(kpis["active_tournaments"], 1)
        self.assertEqual(kpis["total_matches"], 1)

    def test_overview_includes_top_lists(self):
        now = timezone.now()

        club_extra = Club.objects.create(tenant=self.tenant1, name="Clube Tenant 1 Extra")
        Player.objects.create(tenant=self.tenant1, name="Jogador T1B", club=self.club_t1, joined_date=now.date())
        Player.objects.create(tenant=self.tenant1, name="Jogador T1C", club=club_extra, joined_date=now.date())

        PlayerHistory.objects.create(player=self.player_t1, season="2024/2025", goals=7, matches=10, assists=1, club=self.club_t1)
        PlayerHistory.objects.create(player=self.player_t1, season="2023/2024", goals=3, matches=8, assists=0, club=self.club_t1)
        PlayerHistory.objects.create(player=self.player_t2, season="2024/2025", goals=99, matches=30, assists=5, club=self.club_t2)

        request = self.factory.get("/api/dashboard/overview/")
        force_authenticate(request, user=self.user1)

        response = DashboardOverviewView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn("top_clubs_by_players", response.data)
        self.assertIn("top_scorers", response.data)

        top_clubs = response.data["top_clubs_by_players"]
        self.assertTrue(len(top_clubs) >= 1)
        self.assertEqual(top_clubs[0]["id"], str(self.club_t1.id))
        self.assertEqual(top_clubs[0]["players"], 2)

        top_scorers = response.data["top_scorers"]
        self.assertEqual(len(top_scorers), 1)
        self.assertEqual(top_scorers[0]["id"], str(self.player_t1.id))
        self.assertEqual(top_scorers[0]["goals"], 10)
