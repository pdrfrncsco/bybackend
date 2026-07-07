"""
BOLAYETU — Organization DAM isolation tests

Ensures organization branding (logo/banner) is served exclusively via the
DAM (MediaAsset/MediaUsage) and that assets never leak between tenants.

Architecture reference: docs/01-architecture/08A_DIGITAL_ASSET_MANAGEMENT.md
"""

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from core.models import Tenant
from organizations.serializers.organization import (
    OrganizationSerializer,
    PublicOrganizationSerializer,
)
from organizations.services.organization_service import OrganizationService


class OrganizationLogoDamIsolationTest(TestCase):
    """Logo/banner URLs must come from the DAM and stay tenant-scoped."""

    def setUp(self):
        self.tenant_a = Tenant.objects.create(name="Tenant A", is_public=True)
        self.tenant_b = Tenant.objects.create(name="Tenant B", is_public=True)

    def _fake_image(self, name="logo.png"):
        return SimpleUploadedFile(name, b"\x89PNG\r\n\x1a\n", content_type="image/png")

    def test_logo_upload_creates_media_asset_only(self):
        from media_assets.models import MediaAsset

        OrganizationService.upload_logo(tenant=self.tenant_a, file=self._fake_image())

        self.tenant_a.refresh_from_db()
        self.assertFalse(hasattr(self.tenant_a, "logo"))
        self.assertTrue(MediaAsset.objects.filter(owner_id=self.tenant_a.id).exists())

    def test_banner_upload_creates_media_asset_only(self):
        from media_assets.models import MediaAsset

        OrganizationService.upload_banner(tenant=self.tenant_a, file=self._fake_image("banner.png"))

        self.tenant_a.refresh_from_db()
        self.assertFalse(hasattr(self.tenant_a, "banner"))
        self.assertTrue(MediaAsset.objects.filter(owner_id=self.tenant_a.id).exists())

    def test_logo_is_isolated_between_tenants(self):
        OrganizationService.upload_logo(tenant=self.tenant_a, file=self._fake_image())

        data_a = OrganizationSerializer(self.tenant_a).data
        data_b = OrganizationSerializer(self.tenant_b).data

        self.assertTrue(data_a["logo_url"])
        self.assertEqual(data_b["logo_url"], "")
        self.assertNotEqual(data_a["logo_url"], data_b["logo_url"])

    def test_public_serializer_reflects_dam_logo_and_banner(self):
        OrganizationService.upload_logo(tenant=self.tenant_a, file=self._fake_image())
        OrganizationService.upload_banner(tenant=self.tenant_a, file=self._fake_image("banner.png"))

        public_a = PublicOrganizationSerializer(self.tenant_a).data
        public_b = PublicOrganizationSerializer(self.tenant_b).data

        self.assertTrue(public_a["logo_url"])
        self.assertTrue(public_a["banner_url"])
        self.assertEqual(public_b["logo_url"], "")
        self.assertEqual(public_b["banner_url"], "")

    def test_reuploading_logo_replaces_previous_asset_usage(self):
        from media_assets.constants import AssetCategory, OwnerType
        from media_assets.models import MediaUsage

        OrganizationService.upload_logo(tenant=self.tenant_a, file=self._fake_image("first.png"))
        first_usage = MediaUsage.objects.get(
            owner_type=OwnerType.ORGANIZATION,
            owner_id=self.tenant_a.id,
            role=AssetCategory.LOGO,
            is_active=True,
        )

        OrganizationService.upload_logo(tenant=self.tenant_a, file=self._fake_image("second.png"))

        first_usage.refresh_from_db()
        self.assertFalse(first_usage.is_active)

        active_usage = MediaUsage.objects.get(
            owner_type=OwnerType.ORGANIZATION,
            owner_id=self.tenant_a.id,
            role=AssetCategory.LOGO,
            is_active=True,
        )
        self.assertNotEqual(active_usage.id, first_usage.id)
