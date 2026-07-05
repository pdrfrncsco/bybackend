from datetime import timedelta

from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.constants import AccountStatus, MembershipRole
from accounts.models import TenantMembership, User
from clubs.models import Club
from competitions.constants import CompetitionStatus
from competitions.models import Competition, CompetitionRegistration, Match, MatchEvent
from core.models import Tenant
from organizations.models import OrganizationSubscription
from players.models import Player, PlayerRegistration


@override_settings(ALLOWED_HOSTS=["testserver", ".bolayetu.com"])
class DashboardAnalyticsApiTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="admin@bolayetu.com",
            password="SecurePass123!",
            status=AccountStatus.ACTIVE,
            is_email_verified=True,
        )
        self.other_user = User.objects.create_user(
            email="other@bolayetu.com",
            password="SecurePass123!",
            status=AccountStatus.ACTIVE,
            is_email_verified=True,
        )

        self.tenant_a = Tenant.objects.create(
            name="FAF",
            slug="faf",
            subdomain="faf",
            status=Tenant.TenantStatus.ACTIVE,
            is_public=True,
        )
        self.tenant_b = Tenant.objects.create(
            name="Girabola",
            slug="girabola",
            subdomain="girabola",
            status=Tenant.TenantStatus.ACTIVE,
            is_public=True,
        )

        TenantMembership.objects.create(
            user=self.user,
            tenant=self.tenant_a,
            role=MembershipRole.ADMIN,
            is_active=True,
        )
        TenantMembership.objects.create(
            user=self.other_user,
            tenant=self.tenant_b,
            role=MembershipRole.ADMIN,
            is_active=True,
        )

        self.club_a1 = Club.objects.create(name="Petro de Luanda", tenant=self.tenant_a, short_name="APL")
        self.club_a2 = Club.objects.create(name="1º de Agosto", tenant=self.tenant_a, short_name="PRI")
        self.club_b1 = Club.objects.create(name="Sagrada Esperança", tenant=self.tenant_b, short_name="SAG")

        self.comp_a_active = Competition.objects.create(
            name="Girabola 2026",
            tenant=self.tenant_a,
            season="2026/27",
            status=CompetitionStatus.ACTIVE,
        )
        self.comp_a_completed = Competition.objects.create(
            name="Taça FAF 2025",
            tenant=self.tenant_a,
            season="2025/26",
            status=CompetitionStatus.COMPLETED,
        )
        self.comp_b_active = Competition.objects.create(
            name="Liga Regional",
            tenant=self.tenant_b,
            season="2026",
            status=CompetitionStatus.ACTIVE,
        )

        CompetitionRegistration.objects.create(
            competition=self.comp_a_active,
            club=self.club_a1,
            tenant=self.tenant_a,
        )
        CompetitionRegistration.objects.create(
            competition=self.comp_a_active,
            club=self.club_a2,
            tenant=self.tenant_a,
        )
        CompetitionRegistration.objects.create(
            competition=self.comp_b_active,
            club=self.club_b1,
            tenant=self.tenant_b,
        )

        now = timezone.now()
        today = timezone.localdate()
        previous_month_day = today.replace(day=1) - timedelta(days=1)
        previous_month_joined = previous_month_day.replace(day=min(previous_month_day.day, 15))

        self.player_a1 = Player.objects.create(first_name="António", last_name="Manuel")
        self.player_a2 = Player.objects.create(first_name="João", last_name="Silva")
        self.player_a3 = Player.objects.create(first_name="Carlos", last_name="Pedro")
        self.player_b1 = Player.objects.create(first_name="Mateus", last_name="Kiala")

        PlayerRegistration.objects.create(
            player=self.player_a1,
            club=self.club_a1,
            competition=self.comp_a_active,
            tenant=self.tenant_a,
            joined_date=today,
            goals=5,
            matches_played=3,
        )
        PlayerRegistration.objects.create(
            player=self.player_a2,
            club=self.club_a2,
            competition=self.comp_a_active,
            tenant=self.tenant_a,
            joined_date=today,
            goals=3,
            matches_played=3,
        )
        PlayerRegistration.objects.create(
            player=self.player_a3,
            club=self.club_a1,
            competition=self.comp_a_completed,
            tenant=self.tenant_a,
            joined_date=previous_month_joined,
            goals=1,
            matches_played=1,
        )
        PlayerRegistration.objects.create(
            player=self.player_b1,
            club=self.club_b1,
            competition=self.comp_b_active,
            tenant=self.tenant_b,
            joined_date=today,
            goals=7,
            matches_played=4,
        )

        self.match_a_finished = Match.objects.create(
            competition=self.comp_a_active,
            tenant=self.tenant_a,
            home_club=self.club_a1,
            away_club=self.club_a2,
            match_date=now - timedelta(days=1),
            status=Match.MatchStatus.FINISHED,
            home_score=2,
            away_score=1,
        )
        self.match_a_live = Match.objects.create(
            competition=self.comp_a_active,
            tenant=self.tenant_a,
            home_club=self.club_a2,
            away_club=self.club_a1,
            match_date=now,
            status=Match.MatchStatus.LIVE,
            home_score=0,
            away_score=1,
        )
        self.match_a_scheduled = Match.objects.create(
            competition=self.comp_a_active,
            tenant=self.tenant_a,
            home_club=self.club_a1,
            away_club=self.club_a2,
            match_date=now + timedelta(days=2),
            status=Match.MatchStatus.SCHEDULED,
        )
        self.match_a_completed = Match.objects.create(
            competition=self.comp_a_completed,
            tenant=self.tenant_a,
            home_club=self.club_a1,
            away_club=self.club_a2,
            match_date=now - timedelta(days=30),
            status=Match.MatchStatus.FINISHED,
            home_score=1,
            away_score=0,
        )
        self.match_b_finished = Match.objects.create(
            competition=self.comp_b_active,
            tenant=self.tenant_b,
            home_club=self.club_b1,
            away_club=self.club_b1,
            match_date=now - timedelta(days=3),
            status=Match.MatchStatus.FINISHED,
            home_score=3,
            away_score=2,
        )

        MatchEvent.objects.create(
            match=self.match_a_finished,
            tenant=self.tenant_a,
            club=self.club_a1,
            player=self.player_a1,
            event_type=MatchEvent.EventType.GOAL,
            minute=10,
        )
        MatchEvent.objects.create(
            match=self.match_a_finished,
            tenant=self.tenant_a,
            club=self.club_a2,
            player=self.player_a2,
            event_type=MatchEvent.EventType.GOAL,
            minute=40,
        )
        MatchEvent.objects.create(
            match=self.match_a_live,
            tenant=self.tenant_a,
            club=self.club_a1,
            player=self.player_a1,
            event_type=MatchEvent.EventType.PENALTY_SCORED,
            minute=65,
        )
        MatchEvent.objects.create(
            match=self.match_a_completed,
            tenant=self.tenant_a,
            club=self.club_a1,
            player=self.player_a3,
            event_type=MatchEvent.EventType.OWN_GOAL,
            minute=78,
        )
        MatchEvent.objects.create(
            match=self.match_b_finished,
            tenant=self.tenant_b,
            club=self.club_b1,
            player=self.player_b1,
            event_type=MatchEvent.EventType.GOAL,
            minute=15,
        )

        OrganizationSubscription.objects.create(user=self.user, tenant=self.tenant_a, is_active=True)
        OrganizationSubscription.objects.create(user=self.other_user, tenant=self.tenant_b, is_active=True)

    def test_public_stats_returns_real_global_counts(self):
        response = self.client.get(reverse("dashboard-public-stats"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_clubs"], 3)
        self.assertEqual(response.data["total_players"], 4)
        self.assertEqual(response.data["active_tournaments"], 2)
        self.assertEqual(response.data["total_matches"], 5)

    def test_overview_requires_authentication(self):
        response = self.client.get(reverse("dashboard-overview"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_overview_is_scoped_to_authenticated_users_primary_tenant(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(reverse("dashboard-overview"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["kpis"]["total_clubs"], 2)
        self.assertEqual(response.data["kpis"]["total_players"], 3)
        self.assertEqual(response.data["kpis"]["active_tournaments"], 1)
        self.assertEqual(response.data["kpis"]["tournaments_completed"], 1)
        self.assertEqual(response.data["kpis"]["matches_finished"], 2)
        self.assertEqual(response.data["kpis"]["matches_live"], 1)
        self.assertEqual(response.data["kpis"]["matches_scheduled"], 1)
        self.assertEqual(response.data["kpis"]["total_matches"], 4)
        self.assertEqual(response.data["kpis"]["players_this_month"], 2)
        self.assertEqual(response.data["kpis"]["players_last_month"], 1)
        self.assertEqual(response.data["kpis"]["goals_total"], 4)
        self.assertEqual(response.data["kpis"]["organization_subscribers"], 1)
        self.assertEqual(response.data["top_clubs_by_players"][0]["name"], "Petro de Luanda")
        self.assertTrue(all(item["name"] != "Sagrada Esperança" for item in response.data["top_clubs_by_players"]))
        self.assertEqual(response.data["top_scorers"][0]["name"], "António Manuel")
        self.assertTrue(all(item["club"] != "Sagrada Esperança" for item in response.data["top_scorers"]))

    def test_overview_supports_competition_cut(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            reverse("dashboard-overview"),
            {"competition_id": str(self.comp_a_active.id)},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["kpis"]["total_clubs"], 2)
        self.assertEqual(response.data["kpis"]["total_players"], 2)
        self.assertEqual(response.data["kpis"]["active_tournaments"], 1)
        self.assertEqual(response.data["kpis"]["tournaments_completed"], 0)
        self.assertEqual(response.data["kpis"]["matches_finished"], 1)
        self.assertEqual(response.data["kpis"]["matches_live"], 1)
        self.assertEqual(response.data["kpis"]["matches_scheduled"], 1)
        self.assertEqual(response.data["kpis"]["total_matches"], 3)
        self.assertEqual(response.data["kpis"]["goals_total"], 3)
        self.assertEqual(len(response.data["tournaments"]), 1)
        self.assertEqual(response.data["tournaments"][0]["name"], "Girabola 2026")
        self.assertTrue(all(item["club"] != "" for item in response.data["top_scorers"]))

    def test_overview_supports_club_cut(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            reverse("dashboard-overview"),
            {"club_id": str(self.club_a1.id)},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["kpis"]["total_clubs"], 1)
        self.assertEqual(response.data["kpis"]["total_players"], 2)
        self.assertEqual(response.data["kpis"]["active_tournaments"], 1)
        self.assertEqual(response.data["kpis"]["tournaments_completed"], 1)
        self.assertEqual(response.data["kpis"]["total_matches"], 4)
        self.assertEqual(response.data["kpis"]["goals_total"], 3)
        self.assertEqual(len(response.data["top_clubs_by_players"]), 1)
        self.assertEqual(response.data["top_clubs_by_players"][0]["name"], "Petro de Luanda")
        self.assertTrue(all(item["club"] == "Petro de Luanda" for item in response.data["top_scorers"]))

    def test_overview_supports_period_cut(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            reverse("dashboard-overview"),
            {"period": "7d"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["kpis"]["total_players"], 2)
        self.assertEqual(response.data["kpis"]["matches_finished"], 1)
        self.assertEqual(response.data["kpis"]["matches_live"], 1)
        self.assertEqual(response.data["kpis"]["matches_scheduled"], 0)
        self.assertEqual(response.data["kpis"]["total_matches"], 2)
        self.assertEqual(response.data["kpis"]["goals_total"], 3)
        self.assertEqual(response.data["kpis"]["players_last_month"], 0)
        self.assertEqual(len(response.data["upcoming_matches"]), 0)
        self.assertTrue(all(item["name"] != "Carlos Pedro" for item in response.data["top_scorers"]))

    def test_overview_blocks_cross_tenant_subdomain_access(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            reverse("dashboard-overview"),
            HTTP_HOST="girabola.bolayetu.com",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["message"], "You do not belong to this organization.")
