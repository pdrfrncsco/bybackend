from django.test import TestCase, Client
from rest_framework.test import APIClient

from accounts.models import User
from core.models import Tenant
from organizations.models import OrganizationSubscription


class PublicOrganizationsAPITest(TestCase):
    def test_public_organizations_list_returns_200_and_envelope(self):
        client = Client()
        resp = client.get('/api/v1/organizations/public/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get('success') is True)
        self.assertIn('data', data)

    def test_public_organization_detail_marks_authenticated_subscription(self):
        user = User.objects.create_user(
            email="fan@example.com",
            password="test-pass",
            status="active",
            is_email_verified=True,
        )
        tenant = Tenant.objects.create(
            name="Federacao Teste",
            type=Tenant.TenantType.FEDERATION,
            status=Tenant.TenantStatus.ACTIVE,
            is_public=True,
        )
        OrganizationSubscription.objects.create(user=user, tenant=tenant, is_active=True)

        client = APIClient()
        client.force_authenticate(user=user)

        resp = client.get(f"/api/v1/organizations/public/{tenant.slug}/")

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["data"]["is_subscribed"])
