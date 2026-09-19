"""
BOLAYETU — Player Compliance and Performance API Tests
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

from players.models import Player, PlayerComplianceRecord, PlayerPerformanceMetric
from core.models import Tenant
from clubs.models import Club
from transfers.models import Transfer


class ComplianceAndPerformanceAPITestCase(TestCase):
    """Test Compliance, Performance, and Transfer Access for Players."""

    def setUp(self):
        self.client = APIClient()
        User = get_user_model()

        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test-tenant",
            type="club",
        )

        self.club = Club.objects.create(
            tenant=self.tenant,
            name="Test Club",
            short_name="TC",
            slug="test-club",
        )

        self.player_user = User.objects.create_user(
            email="athlete@test.com",
            password="password123",
            first_name="Athlete",
            last_name="Test",
        )

        self.player = Player.objects.create(
            user=self.player_user,
            first_name="Athlete",
            last_name="Test",
            date_of_birth=date(2002, 5, 20),
            nationality="Angola",
            primary_position="cm",
        )

    def test_compliance_endpoints(self):
        """Test GET compliance records and compliance summary."""
        self.client.force_authenticate(user=self.player_user)

        # Create sample compliance record
        PlayerComplianceRecord.objects.create(
            player=self.player,
            rule_type=PlayerComplianceRecord.RuleType.WORK_PERMIT,
            rule_reference="RSTP Art. 19",
            priority=PlayerComplianceRecord.Priority.HIGH,
            status=PlayerComplianceRecord.ComplianceStatus.COMPLIANT,
            description="Autorização de trabalho emitida.",
            deadline=date.today() + timedelta(days=90),
        )

        # 1. List
        res_list = self.client.get(f"/api/v1/players/{self.player.id}/compliance/")
        self.assertEqual(res_list.status_code, 200)
        data_list = res_list.json()
        self.assertIsInstance(data_list, list)
        self.assertEqual(len(data_list), 1)
        self.assertEqual(data_list[0]["rule_type"], "work_permit")

        # 2. Summary
        res_summary = self.client.get(f"/api/v1/players/{self.player.id}/compliance/status/")
        self.assertEqual(res_summary.status_code, 200)
        data_summary = res_summary.json()
        self.assertEqual(data_summary["total"], 1)
        self.assertEqual(data_summary["compliant"], 1)
        self.assertEqual(data_summary["non_compliant"], 0)

    def test_performance_endpoints(self):
        """Test GET performance metrics and summary."""
        self.client.force_authenticate(user=self.player_user)

        # Create sample performance metric
        PlayerPerformanceMetric.objects.create(
            player=self.player,
            recorded_at=timezone.now(),
            metric_type=PlayerPerformanceMetric.MetricType.MAX_SPEED,
            value=Decimal("33.40"),
            unit="km/h",
            source=PlayerPerformanceMetric.MetricSource.GPS,
        )

        # 1. Metrics list
        res_metrics = self.client.get(f"/api/v1/players/{self.player.id}/performance-metrics/")
        self.assertEqual(res_metrics.status_code, 200)
        data_metrics = res_metrics.json()
        self.assertEqual(len(data_metrics), 1)
        self.assertEqual(data_metrics[0]["metric_type"], "max_speed")

        # 2. Summary
        res_summary = self.client.get(f"/api/v1/players/{self.player.id}/performance/summary/")
        self.assertEqual(res_summary.status_code, 200)
        data_summary = res_summary.json()
        self.assertIn("speed_metrics", data_summary)
        self.assertEqual(data_summary["speed_metrics"]["category"], "speed")
        self.assertGreater(data_summary["speed_metrics"]["max"], 0)

    def test_authenticated_player_can_query_transfers(self):
        """Test that an authenticated athlete without TenantMembership can query transfers."""
        self.client.force_authenticate(user=self.player_user)

        res = self.client.get(f"/api/v1/transfers/?player_id={self.player.id}")
        self.assertEqual(res.status_code, 200)

    def test_contracts_list_and_create(self):
        """Test that an athlete can create and list contracts with derived tenant."""
        self.client.force_authenticate(user=self.player_user)

        # 1. Create contract
        payload = {
            "club": str(self.club.id),
            "contract_type": "professional",
            "status": "draft",
            "start_date": "2026-07-01",
            "end_date": "2028-06-30",
            "salary": "120000.00",
            "currency": "USD",
            "release_clause": "500000.00",
            "has_image_rights": True,
        }
        res_create = self.client.post(
            f"/api/v1/players/{self.player.id}/contracts/",
            data=payload,
            format="json",
        )
        self.assertEqual(res_create.status_code, 201)
        created_data = res_create.json()
        self.assertEqual(created_data["contract_type"], "professional")
        self.assertEqual(str(created_data["club"]), str(self.club.id))

        # 2. List contracts
        res_list = self.client.get(f"/api/v1/players/{self.player.id}/contracts/")
        self.assertEqual(res_list.status_code, 200)
        data = res_list.json()
        inner_data = data.get("data", data)
        data_list = inner_data.get("results", inner_data) if isinstance(inner_data, dict) else inner_data
        self.assertEqual(len(data_list), 1)
        self.assertEqual(data_list[0]["club_name"], "Test Club")
        self.assertEqual(str(data_list[0]["club"]), str(self.club.id))
        self.assertEqual(data_list[0]["is_active"], False)  # draft

