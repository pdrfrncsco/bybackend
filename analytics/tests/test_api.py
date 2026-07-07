from datetime import timedelta

from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.constants import AccountStatus, MembershipRole
from accounts.models import TenantMembership, User
from analytics.models import KPISnapshot, GeneratedReport
from analytics.constants import MetricKey, ReportType, ReportStatus, ReportFormat
from analytics.services.kpi_service import KPIService
from analytics.services.report_service import ReportService
from analytics.tasks import snapshot_kpis_daily_task
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


@override_settings(ALLOWED_HOSTS=["testserver", ".bolayetu.com"])
class SpecializedDashboardApiTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="admin@bolayetu.com",
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
        TenantMembership.objects.create(
            user=self.user,
            tenant=self.tenant_a,
            role=MembershipRole.ADMIN,
            is_active=True,
        )
        self.club = Club.objects.create(name="Petro de Luanda", tenant=self.tenant_a, short_name="APL")
        self.competition = Competition.objects.create(
            name="Girabola 2026",
            tenant=self.tenant_a,
            season="2026/27",
            status=CompetitionStatus.ACTIVE,
        )

    def test_organization_dashboard_success(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("dashboard-organization"), HTTP_HOST="faf.bolayetu.com")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("kpis", response.data)

    def test_club_dashboard_success(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            reverse("dashboard-club", kwargs={"club_id": self.club.id}),
            HTTP_HOST="faf.bolayetu.com",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_competition_dashboard_success(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            reverse("dashboard-competition", kwargs={"competition_id": self.competition.id}),
            HTTP_HOST="faf.bolayetu.com",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_comparative_analytics_success(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            reverse("analytics-compare"),
            {"period": "30d"},
            HTTP_HOST="faf.bolayetu.com",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("comparison", response.data)



@override_settings(ALLOWED_HOSTS=["testserver", ".bolayetu.com"])
class ReportsApiTest(APITestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(
            email="admin_a@bolayetu.com",
            password="SecurePass123!",
            status=AccountStatus.ACTIVE,
            is_email_verified=True,
        )
        self.user_b = User.objects.create_user(
            email="admin_b@bolayetu.com",
            password="SecurePass123!",
            status=AccountStatus.ACTIVE,
            is_email_verified=True,
        )
        self.tenant_a = Tenant.objects.create(
            name="Tenant A",
            slug="tenant-a",
            subdomain="tenant-a",
            status=Tenant.TenantStatus.ACTIVE,
            is_public=True,
        )
        self.tenant_b = Tenant.objects.create(
            name="Tenant B",
            slug="tenant-b",
            subdomain="tenant-b",
            status=Tenant.TenantStatus.ACTIVE,
            is_public=True,
        )
        TenantMembership.objects.create(
            user=self.user_a,
            tenant=self.tenant_a,
            role=MembershipRole.ADMIN,
            is_active=True,
        )
        TenantMembership.objects.create(
            user=self.user_b,
            tenant=self.tenant_b,
            role=MembershipRole.ADMIN,
            is_active=True,
        )

    def test_request_report_generates_completed_report_due_to_eager_celery(self):
        self.client.force_authenticate(user=self.user_a)
        payload = {
            "name": "FAF Organization Report",
            "report_type": ReportType.ORGANIZATION_PERFORMANCE,
            "format": ReportFormat.CSV,
            "filters": {},
        }
        response = self.client.post(
            reverse("report-list-create"),
            payload,
            format="json",
            HTTP_HOST="tenant-a.bolayetu.com",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], payload["name"])
        self.assertEqual(response.data["status"], ReportStatus.PENDING)

        # Fetch list
        response_list = self.client.get(
            reverse("report-list-create"),
            HTTP_HOST="tenant-a.bolayetu.com",
        )
        self.assertEqual(response_list.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_list.data), 1)

        # Retrieve detail
        report_id = response.data["id"]
        response_detail = self.client.get(
            reverse("report-detail", kwargs={"pk": report_id}),
            HTTP_HOST="tenant-a.bolayetu.com",
        )
        self.assertEqual(response_detail.status_code, status.HTTP_200_OK)
        self.assertEqual(response_detail.data["status"], ReportStatus.COMPLETED)

        # Delete
        response_delete = self.client.delete(
            reverse("report-detail", kwargs={"pk": report_id}),
            HTTP_HOST="tenant-a.bolayetu.com",
        )
        self.assertEqual(response_delete.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(GeneratedReport.objects.filter(id=report_id).exists())

    def test_report_tenant_isolation(self):
        # Create a report for Tenant A
        report = ReportService.request_report(
            tenant=self.tenant_a,
            name="Report A",
            report_type=ReportType.ORGANIZATION_PERFORMANCE,
            format=ReportFormat.CSV,
            filters={},
            created_by=self.user_a,
        )

        # Attempt to access using Tenant B user
        self.client.force_authenticate(user=self.user_b)
        response_detail = self.client.get(
            reverse("report-detail", kwargs={"pk": report.id}),
            HTTP_HOST="tenant-b.bolayetu.com",
        )
        self.assertEqual(response_detail.status_code, status.HTTP_404_NOT_FOUND)

    def test_report_download_success(self):
        from media_assets.models import MediaAsset
        from media_assets.constants import AssetCategory, AssetStatus, AssetType
        self.client.force_authenticate(user=self.user_a)

        # Create asset
        asset = MediaAsset.objects.create(
            name="Report Test",
            tenant=self.tenant_a,
            original_filename="report_test.csv",
            extension="csv",
            size_bytes=123,
            mime_type="text/csv",
            asset_type=AssetType.DOCUMENT,
            category=AssetCategory.DOCUMENT,
            uploaded_by=self.user_a,
            status=AssetStatus.READY,
        )

        # Create report
        report = GeneratedReport.objects.create(
            tenant=self.tenant_a,
            name="Download Report",
            report_type=ReportType.ORGANIZATION_PERFORMANCE,
            format=ReportFormat.CSV,
            status=ReportStatus.COMPLETED,
            file=asset,
            created_by=self.user_a,
        )

        response = self.client.get(
            reverse("report-download", kwargs={"pk": report.id}),
            HTTP_HOST="tenant-a.bolayetu.com",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("download_url", response.data)
        self.assertEqual(response.data["filename"], "report_test.csv")



@override_settings(ALLOWED_HOSTS=["testserver", ".bolayetu.com"])
class KPISnapshotTest(APITestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(
            name="FAF",
            slug="faf",
            subdomain="faf",
            status=Tenant.TenantStatus.ACTIVE,
            is_public=True,
        )

    def test_snapshot_kpis_creation(self):
        # Snapshot KPIs
        KPIService.snapshot_all_tenants()

        # Check snapshots exist
        global_snapshots = KPISnapshot.objects.filter(tenant=None)
        self.assertTrue(global_snapshots.exists())
        self.assertEqual(
            global_snapshots.filter(metric_key=MetricKey.TOTAL_PLAYERS).first().value,
            0.0,  # No players in test DB setup for this specific class
        )

        tenant_snapshots = KPISnapshot.objects.filter(tenant=self.tenant)
        self.assertTrue(tenant_snapshots.exists())

    def test_snapshot_periodic_task(self):
        # Run daily task
        res = snapshot_kpis_daily_task.delay()
        self.assertEqual(res.result["status"], "success")
        self.assertTrue(KPISnapshot.objects.exists())
