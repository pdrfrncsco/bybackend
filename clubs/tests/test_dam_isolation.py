"""
BOLAYETU — Club DAM isolation tests

Ensures club branding (logo) is served exclusively via the DAM
(MediaAsset/MediaUsage) and that assets never leak between clubs/tenants.

Architecture reference: docs/01-architecture/08A_DIGITAL_ASSET_MANAGEMENT.md
"""

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from clubs.serializers.club import ClubSerializer, PublicClubSerializer
from clubs.services import ClubService
from core.models import Tenant


class ClubLogoDamIsolationTest(TestCase):
    """Club logo URLs must come from the DAM and stay scoped per club."""

    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Org")
        self.club_a = ClubService.create_club(tenant=self.tenant, name="Club A", is_public=True)
        self.club_b = ClubService.create_club(tenant=self.tenant, name="Club B", is_public=True)

    def _fake_image(self, name="logo.png"):
        return SimpleUploadedFile(name, b"\x89PNG\r\n\x1a\n", content_type="image/png")

    def test_logo_upload_creates_media_asset_only(self):
        from media_assets.models import MediaAsset

        ClubService.upload_logo(club=self.club_a, file=self._fake_image())

        self.club_a.refresh_from_db()
        self.assertFalse(hasattr(self.club_a, "logo"))
        self.assertTrue(MediaAsset.objects.filter(owner_id=self.club_a.id).exists())

    def test_logo_is_isolated_between_clubs(self):
        ClubService.upload_logo(club=self.club_a, file=self._fake_image())

        data_a = ClubSerializer(self.club_a).data
        data_b = ClubSerializer(self.club_b).data

        self.assertTrue(data_a["logo_url"])
        self.assertEqual(data_b["logo_url"], "")
        self.assertNotEqual(data_a["logo_url"], data_b["logo_url"])

    def test_public_serializer_reflects_dam_logo(self):
        ClubService.upload_logo(club=self.club_a, file=self._fake_image())

        public_a = PublicClubSerializer(self.club_a).data
        public_b = PublicClubSerializer(self.club_b).data

        self.assertTrue(public_a["logo_url"])
        self.assertEqual(public_b["logo_url"], "")

    def test_reuploading_logo_replaces_previous_asset_usage(self):
        from media_assets.constants import AssetCategory, OwnerType
        from media_assets.models import MediaUsage

        ClubService.upload_logo(club=self.club_a, file=self._fake_image("first.png"))
        first_usage = MediaUsage.objects.get(
            owner_type=OwnerType.CLUB,
            owner_id=self.club_a.id,
            role=AssetCategory.LOGO,
            is_active=True,
        )

        ClubService.upload_logo(club=self.club_a, file=self._fake_image("second.png"))

        first_usage.refresh_from_db()
        self.assertFalse(first_usage.is_active)
