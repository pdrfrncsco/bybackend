from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import Tenant
from assinaturas.models import SubscriptionPlan, Subscription
from .models import ReportJob


User = get_user_model()


class ReportsApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.tenant = Tenant.objects.create(name="Tenant Test", slug="tenant-test")
        self.user = User.objects.create_user(
            username="manager",
            email="manager@example.com",
            password="pass1234",
            tenant=self.tenant,
            role="manager",
        )
        self.client.force_authenticate(user=self.user)

    def _create_subscription(self, plan_type):
        plan = SubscriptionPlan.objects.create(
            code=f"{plan_type}-plan",
            name=f"{plan_type.title()} Plan",
            target_type="tenant",
            plan_type=plan_type,
            price_amount=1000,
            billing_period="monthly",
            is_active=True,
        )
        Subscription.objects.create(
            subscriber_type="tenant",
            tenant=self.tenant,
            plan=plan,
            status="active",
            billing_period=plan.billing_period,
            amount=plan.price_amount,
        )

    def test_definitions_endpoint_returns_available_reports(self):
        response = self.client.get("/api/reports/definitions/")

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        ids = {item["id"] for item in response.data}
        self.assertIn("standings", ids)
        self.assertIn("player_stats", ids)

    def test_generate_creates_report_job_and_file(self):
        payload = {
            "report_type": "standings",
            "format": "csv",
            "params": {},
        }

        response = self.client.post("/api/reports/generate/", payload, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(ReportJob.objects.count(), 1)

        job = ReportJob.objects.first()
        self.assertEqual(job.tenant, self.tenant)
        self.assertEqual(job.user, self.user)
        self.assertEqual(job.report_type, "standings")
        self.assertEqual(job.status, "completed")
        self.assertTrue(job.file.name)

        self.assertIn("file_url", response.data)
        self.assertIsNotNone(response.data["file_url"])

    def test_free_plan_cannot_generate_pro_or_advanced_report(self):
        self._create_subscription("free")

        payload = {
            "report_type": "club_performance",
            "format": "csv",
            "params": {},
        }

        response = self.client.post("/api/reports/generate/", payload, format="json")

        self.assertEqual(response.status_code, 403)
        self.assertTrue("detail" in response.data or "error" in response.data)

    def test_pro_plan_can_generate_pro_reports(self):
        self._create_subscription("pro")

        payload = {
            "report_type": "club_performance",
            "format": "csv",
            "params": {},
        }

        response = self.client.post("/api/reports/generate/", payload, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(ReportJob.objects.count(), 1)

    def test_pro_plan_cannot_generate_advanced_report(self):
        self._create_subscription("pro")

        payload = {
            "report_type": "match_sheet",
            "format": "csv",
            "params": {"match": "1"},
        }

        response = self.client.post("/api/reports/generate/", payload, format="json")

        self.assertEqual(response.status_code, 403)
        self.assertTrue("detail" in response.data or "error" in response.data)

    def test_premium_plan_can_generate_advanced_report(self):
        self._create_subscription("premium")

        payload = {
            "report_type": "match_sheet",
            "format": "csv",
            "params": {"match": "1"},
        }

        response = self.client.post("/api/reports/generate/", payload, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(ReportJob.objects.count(), 1)

    def test_history_returns_only_current_user_jobs(self):
        other_tenant = Tenant.objects.create(name="Other Tenant", slug="other-tenant")
        other_user = User.objects.create_user(
            username="other",
            email="other@example.com",
            password="pass1234",
            tenant=other_tenant,
            role="manager",
        )

        ReportJob.objects.create(
            tenant=self.tenant,
            user=self.user,
            report_type="standings",
            format="csv",
            status="completed",
        )
        ReportJob.objects.create(
            tenant=other_tenant,
            user=other_user,
            report_type="standings",
            format="csv",
            status="completed",
        )

        response = self.client.get("/api/reports/history/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["report_type"], "standings")
