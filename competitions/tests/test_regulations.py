from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import TenantMembership
from competitions.models import Competition, CompetitionRegulation
from competitions.services import CompetitionRegulationService
from core.models import Tenant
from media_assets.constants import AssetCategory, OwnerType
from media_assets.models import MediaUsage

User = get_user_model()


class CompetitionRegulationsAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email="admin@bolayetu.com", password="SecurePass123!", status="active")
        self.tenant = Tenant.objects.create(
            name="Angolan Football Association",
            slug="faf",
            subdomain="faf",
            status=Tenant.TenantStatus.ACTIVE,
            is_public=True,
        )
        TenantMembership.objects.create(user=self.user, tenant=self.tenant, role="owner", is_active=True)
        self.client.force_authenticate(user=self.user)
        self.competition = Competition.objects.create(
            tenant=self.tenant,
            name="Girabola",
            competition_type="league",
            season="2025/26",
            status="active",
        )

    def test_create_regulation_uploads_document(self):
        url = f"/api/v1/competitions/{self.competition.id}/regulations/"
        payload = {
            "title": "Regulamento Geral",
            "summary": "Regras da competição",
            "version": "1.0",
            "status": "published",
            "document": SimpleUploadedFile("regulamento.pdf", b"%PDF-1.4 fake", content_type="application/pdf"),
        }

        response = self.client.post(url, payload, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        regulation = CompetitionRegulation.objects.get(competition=self.competition, title="Regulamento Geral")
        usage = MediaUsage.objects.get(
            owner_type=OwnerType.COMPETITION_REGULATION,
            owner_id=regulation.id,
            role=AssetCategory.DOCUMENT,
            is_active=True,
        )
        self.assertTrue(usage.asset.public_url)
        self.assertTrue(response.data["data"]["document_url"])

    def test_public_list_returns_regulations(self):
        CompetitionRegulationService.create_regulation(
            tenant=self.tenant,
            competition=self.competition,
            title="Regulamento Geral",
            summary="Regras da competição",
            version="1.0",
            document=SimpleUploadedFile("regulamento.pdf", b"%PDF-1.4 fake", content_type="application/pdf"),
            uploaded_by=self.user,
        )

        self.client.force_authenticate(user=None)
        response = self.client.get(f"/api/v1/competitions/{self.competition.id}/regulations/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["data"][0]["title"], "Regulamento Geral")
