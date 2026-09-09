from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import TenantMembership
from core.models import Tenant
from media_assets.constants import AssetCategory, AssetType, AssetVisibility, OwnerType
from media_assets.models import MediaAsset, MediaUsage


User = get_user_model()


class MediaAssetTenantAccessTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.tenant_a = Tenant.objects.create(name="Tenant A", slug="tenant-a")
        self.tenant_b = Tenant.objects.create(name="Tenant B", slug="tenant-b")

        self.user_a = User.objects.create_user(
            email="media-a@bolayetu.com",
            password="SecurePass123!",
            status="active",
        )
        self.user_b = User.objects.create_user(
            email="media-b@bolayetu.com",
            password="SecurePass123!",
            status="active",
        )

        TenantMembership.objects.create(
            user=self.user_a,
            tenant=self.tenant_a,
            role="owner",
            is_active=True,
        )
        TenantMembership.objects.create(
            user=self.user_b,
            tenant=self.tenant_b,
            role="owner",
            is_active=True,
        )

        self.asset_a = self.create_asset(
            tenant=self.tenant_a,
            uploaded_by=self.user_a,
            name="Tenant A Logo",
        )
        self.asset_b = self.create_asset(
            tenant=self.tenant_b,
            uploaded_by=self.user_b,
            name="Tenant B Logo",
        )

    def create_asset(self, *, tenant, uploaded_by, name):
        return MediaAsset.objects.create(
            name=name,
            asset_type=AssetType.IMAGE,
            category=AssetCategory.LOGO,
            original_filename="logo.png",
            mime_type="image/png",
            extension="png",
            size_bytes=64,
            checksum_sha256="a" * 64,
            bucket="test",
            object_key=f"tenant/{tenant.slug}/organization/logo/logo.png",
            cdn_url=f"/media/tenant/{tenant.slug}/organization/logo/logo.png",
            owner_type=OwnerType.ORGANIZATION,
            owner_id=tenant.id,
            tenant=tenant,
            visibility=AssetVisibility.PUBLIC,
            uploaded_by=uploaded_by,
        )

    def test_user_can_retrieve_asset_from_own_tenant(self):
        self.client.force_authenticate(user=self.user_a)

        response = self.client.get(f"/api/v1/media/{self.asset_a.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["success"], True)
        self.assertEqual(response.data["data"]["id"], str(self.asset_a.id))

    def test_user_cannot_retrieve_asset_from_other_tenant(self):
        self.client.force_authenticate(user=self.user_a)

        response = self.client.get(f"/api/v1/media/{self.asset_b.id}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_cannot_delete_asset_from_other_tenant(self):
        self.client.force_authenticate(user=self.user_a)

        response = self.client.delete(f"/api/v1/media/{self.asset_b.id}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.asset_b.refresh_from_db()
        self.assertNotEqual(self.asset_b.status, "deleted")

    def test_user_cannot_get_signed_url_for_other_tenant_asset(self):
        self.client.force_authenticate(user=self.user_a)

        response = self.client.get(f"/api/v1/media/{self.asset_b.id}/signed-url/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_upload_rejects_tenant_without_membership(self):
        self.client.force_authenticate(user=self.user_a)
        file = SimpleUploadedFile(
            "logo.png",
            b"not-used-because-request-is-rejected-before-storage",
            content_type="image/png",
        )

        response = self.client.post(
            "/api/v1/media/upload/",
            {
                "file": file,
                "tenant_id": str(self.tenant_b.id),
                "owner_type": OwnerType.ORGANIZATION,
                "owner_id": str(self.tenant_b.id),
                "role": AssetCategory.LOGO,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_can_list_and_associate_asset_usage_in_own_tenant(self):
        self.client.force_authenticate(user=self.user_a)

        list_response = self.client.get(
            "/api/v1/media/usage/",
            {"owner_type": OwnerType.ORGANIZATION, "owner_id": str(self.tenant_a.id)},
        )

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.data["data"]["results"], [])

        create_response = self.client.post(
            "/api/v1/media/usage/",
            {
                "asset_id": str(self.asset_a.id),
                "owner_type": OwnerType.ORGANIZATION,
                "owner_id": str(self.tenant_a.id),
                "role": AssetCategory.LOGO,
            },
            format="json",
        )

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(create_response.data["data"]["asset"]["id"], str(self.asset_a.id))
        self.assertTrue(MediaUsage.objects.filter(asset=self.asset_a, is_active=True).exists())

    def test_user_cannot_associate_asset_from_other_tenant(self):
        self.client.force_authenticate(user=self.user_a)

        response = self.client.post(
            "/api/v1/media/usage/",
            {
                "asset_id": str(self.asset_b.id),
                "owner_type": OwnerType.ORGANIZATION,
                "owner_id": str(self.tenant_a.id),
                "role": AssetCategory.LOGO,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(MediaUsage.objects.filter(asset=self.asset_b).exists())

    def test_user_can_unlink_usage_without_deleting_asset(self):
        usage = MediaUsage.replace_for(
            owner_type=OwnerType.ORGANIZATION,
            owner_id=self.tenant_a.id,
            role=AssetCategory.LOGO,
            new_asset=self.asset_a,
        )
        self.client.force_authenticate(user=self.user_a)

        response = self.client.delete(f"/api/v1/media/usage/{usage.id}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        usage.refresh_from_db()
        self.asset_a.refresh_from_db()
        self.assertFalse(usage.is_active)
        self.assertNotEqual(self.asset_a.status, "deleted")

    def test_media_usage_link_for_appends_for_gallery_and_replaces_for_logo(self):
        # Collection role: gallery
        usage_g1 = MediaUsage.link_for(
            owner_type=OwnerType.ORGANIZATION,
            owner_id=self.tenant_a.id,
            role="gallery",
            asset=self.asset_a,
        )
        usage_g2 = MediaUsage.link_for(
            owner_type=OwnerType.ORGANIZATION,
            owner_id=self.tenant_a.id,
            role="gallery",
            asset=self.asset_b,
        )
        active_gallery = MediaUsage.objects.filter(
            owner_type=OwnerType.ORGANIZATION,
            owner_id=self.tenant_a.id,
            role="gallery",
            is_active=True,
        )
        self.assertEqual(active_gallery.count(), 2)

        # Singleton role: logo
        usage_l1 = MediaUsage.link_for(
            owner_type=OwnerType.ORGANIZATION,
            owner_id=self.tenant_a.id,
            role="logo",
            asset=self.asset_a,
        )
        self.assertTrue(usage_l1.is_active)

        usage_l2 = MediaUsage.link_for(
            owner_type=OwnerType.ORGANIZATION,
            owner_id=self.tenant_a.id,
            role="logo",
            asset=self.asset_b,
        )
        usage_l1.refresh_from_db()
        self.assertFalse(usage_l1.is_active)
        self.assertTrue(usage_l2.is_active)
        active_logos = MediaUsage.objects.filter(
            owner_type=OwnerType.ORGANIZATION,
            owner_id=self.tenant_a.id,
            role="logo",
            is_active=True,
        )
        self.assertEqual(active_logos.count(), 1)

    def test_rbac_asset_deletion_inside_tenant(self):
        member_user = User.objects.create_user(
            email="member@bolayetu.com",
            password="SecurePass123!",
            status="active",
        )
        TenantMembership.objects.create(
            user=member_user,
            tenant=self.tenant_a,
            role="member",
            is_active=True,
        )
        asset_by_member = self.create_asset(
            tenant=self.tenant_a,
            uploaded_by=member_user,
            name="Member Uploaded",
        )

        # Member cannot delete asset uploaded by owner
        self.client.force_authenticate(user=member_user)
        res_fail = self.client.delete(f"/api/v1/media/{self.asset_a.id}/")
        self.assertEqual(res_fail.status_code, status.HTTP_403_FORBIDDEN)

        # Member CAN delete asset uploaded by themselves
        from unittest.mock import patch
        with patch("media_assets.services.media_service.MediaAssetService.delete_asset") as mock_del:
            res_member_del = self.client.delete(f"/api/v1/media/{asset_by_member.id}/")
            self.assertEqual(res_member_del.status_code, status.HTTP_200_OK)
            self.assertTrue(mock_del.called)

        # Owner CAN delete asset uploaded by member
        self.client.force_authenticate(user=self.user_a)
        with patch("media_assets.services.media_service.MediaAssetService.delete_asset") as mock_del:
            res_owner_del = self.client.delete(f"/api/v1/media/{asset_by_member.id}/")
            self.assertEqual(res_owner_del.status_code, status.HTTP_200_OK)
            self.assertTrue(mock_del.called)

    def test_player_user_can_upload_and_list_media_without_tenant(self):
        from unittest.mock import patch
        from players.models import Player

        player_user = User.objects.create_user(
            email="athlete@bolayetu.com",
            password="SecurePass123!",
            status="active",
        )
        player = Player.objects.create(
            first_name="Athlete",
            last_name="One",
            user=player_user,
        )
        other_player = Player.objects.create(
            first_name="Athlete",
            last_name="Two",
        )

        self.client.force_authenticate(user=player_user)

        # Upload without tenant for own player profile succeeds
        file = SimpleUploadedFile("avatar.jpg", b"fake-data", content_type="image/jpeg")
        dummy_asset = self.create_asset(
            tenant=self.tenant_a,
            uploaded_by=player_user,
            name="Athlete Avatar",
        )
        with patch("media_assets.services.media_service.MediaAssetService.upload_for_owner", return_value=dummy_asset):
            res_upload = self.client.post(
                "/api/v1/media/upload/",
                {
                    "file": file,
                    "owner_type": OwnerType.PLAYER,
                    "owner_id": str(player.id),
                    "role": "avatar",
                },
                format="multipart",
            )
            self.assertEqual(res_upload.status_code, status.HTTP_201_CREATED)

        # Upload for another player's profile is forbidden
        file2 = SimpleUploadedFile("avatar.jpg", b"fake-data", content_type="image/jpeg")
        res_forbidden = self.client.post(
            "/api/v1/media/upload/",
            {
                "file": file2,
                "owner_type": OwnerType.PLAYER,
                "owner_id": str(other_player.id),
                "role": "avatar",
            },
            format="multipart",
        )
        self.assertEqual(res_forbidden.status_code, status.HTTP_403_FORBIDDEN)

        # List scoped to own player profile succeeds
        res_list = self.client.get(
            "/api/v1/media/",
            {"owner_type": OwnerType.PLAYER, "owner_id": str(player.id)},
        )
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)

        # List for another player profile is forbidden
        res_list_other = self.client.get(
            "/api/v1/media/",
            {"owner_type": OwnerType.PLAYER, "owner_id": str(other_player.id)},
        )
        self.assertEqual(res_list_other.status_code, status.HTTP_403_FORBIDDEN)
