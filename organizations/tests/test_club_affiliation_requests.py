from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import TenantMembership
from clubs.models import Club, ClubAffiliationRequest
from core.models import Tenant

User = get_user_model()


class ClubAffiliationRequestAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email="requester@bolayetu.com", password="SecurePass123!", status="active")
        self.admin = User.objects.create_user(email="admin@bolayetu.com", password="SecurePass123!", status="active")
        self.tenant = Tenant.objects.create(
            name="Angolan Football Association",
            slug="faf",
            subdomain="faf",
            status=Tenant.TenantStatus.ACTIVE,
            is_public=True,
        )
        TenantMembership.objects.create(user=self.admin, tenant=self.tenant, role="owner", is_active=True)

    def test_submit_club_affiliation_request(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            "/api/v1/organizations/public/faf/club-requests/",
            {
                "name": "Academia Futuro",
                "city": "Luanda",
                "country": "Angola",
                "email": "contact@academiafuturo.ao",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertTrue(ClubAffiliationRequest.objects.filter(tenant=self.tenant, name="Academia Futuro").exists())

    def test_review_club_affiliation_request_approve_creates_club(self):
        request_obj = ClubAffiliationRequest.objects.create(
            tenant=self.tenant,
            submitted_by=self.user,
            name="Academia Futuro",
            city="Luanda",
            country="Angola",
            status=ClubAffiliationRequest.Status.PENDING,
        )

        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/api/v1/organizations/me/club-requests/{request_obj.id}/",
            {"approve": True, "review_notes": "Aprovado"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        request_obj.refresh_from_db()
        self.assertEqual(request_obj.status, ClubAffiliationRequest.Status.APPROVED)
        self.assertIsNotNone(request_obj.club)
        self.assertTrue(Club.objects.filter(id=request_obj.club_id, tenant=self.tenant).exists())

    def test_review_club_affiliation_request_rejects(self):
        request_obj = ClubAffiliationRequest.objects.create(
            tenant=self.tenant,
            submitted_by=self.user,
            name="Academia Futuro 2",
            city="Luanda",
            country="Angola",
            status=ClubAffiliationRequest.Status.PENDING,
        )

        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/api/v1/organizations/me/club-requests/{request_obj.id}/",
            {"approve": False, "review_notes": "Falta documentação"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        request_obj.refresh_from_db()
        self.assertEqual(request_obj.status, ClubAffiliationRequest.Status.REJECTED)
        self.assertIsNone(request_obj.club)
