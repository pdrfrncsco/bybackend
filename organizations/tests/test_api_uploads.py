"""
BOLAYETU — Organization upload API tests

Tests POST /api/v1/organizations/me/logo/ and /api/v1/organizations/me/banner/
"""

import os
from importlib import import_module

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.constants import AccountStatus, MembershipRole
from accounts.models import TenantMembership, User
from core.models import Tenant


class OrganizationUploadAPITest(APITestCase):
    """End-to-end tests for organization logo/banner upload endpoints."""

    def setUp(self):
        # Create an active user and tenant, then make the user an owner/admin of the tenant
        self.password = "SecurePassword123!"
        self.user = User.objects.create_user(
            email="upload_api@bolayetu.com",
            password=self.password,
            status=AccountStatus.ACTIVE,
            is_email_verified=True,
        )

        self.tenant = Tenant.objects.create(name="Upload Test Org")

        TenantMembership.objects.create(
            user=self.user,
            tenant=self.tenant,
            role=MembershipRole.OWNER,
            invited_by=self.user,
            is_active=True,
        )

        # Authenticate and set token
        login_url = reverse("login")
        resp = self.client.post(login_url, {"email": self.user.email, "password": self.password}, format="json")
        token = resp.data["data"]["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_upload_banner(self):
        """Banner upload should create a MediaAsset/MediaUsage (DAM), not the legacy field."""
        from media_assets.constants import AssetCategory, OwnerType
        from media_assets.models import MediaUsage

        url = reverse("organization-banner")
        content = SimpleUploadedFile("banner.jpg", b"\x47\x49\x46\x38\x39\x61", content_type="image/jpeg")
        resp = self.client.post(url, {"banner": content}, format="multipart")

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["success"])

        # Legacy ImageField no longer exists — DAM is the single source of truth.
        self.tenant.refresh_from_db()
        self.assertFalse(hasattr(self.tenant, "banner"))

        usage = MediaUsage.objects.get(
            owner_type=OwnerType.ORGANIZATION,
            owner_id=self.tenant.id,
            role=AssetCategory.BANNER,
            is_active=True,
        )
        self.assertTrue(usage.asset.public_url)
        self.assertTrue(resp.data["data"]["banner_url"])

    def test_upload_logo(self):
        """Logo upload should create a MediaAsset/MediaUsage (DAM), not the legacy field."""
        from media_assets.constants import AssetCategory, OwnerType
        from media_assets.models import MediaUsage

        url = reverse("organization-logo")
        content = SimpleUploadedFile("logo.png", b"\x89PNG\r\n\x1a\n", content_type="image/png")
        resp = self.client.post(url, {"logo": content}, format="multipart")

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["success"])

        # Legacy ImageField no longer exists — DAM is the single source of truth.
        self.tenant.refresh_from_db()
        self.assertFalse(hasattr(self.tenant, "logo"))

        usage = MediaUsage.objects.get(
            owner_type=OwnerType.ORGANIZATION,
            owner_id=self.tenant.id,
            role=AssetCategory.LOGO,
            is_active=True,
        )
        self.assertTrue(usage.asset.public_url)
        self.assertTrue(resp.data["data"]["logo_url"])
