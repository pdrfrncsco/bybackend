"""
BOLAYETU — Organization upload API tests

Tests POST /api/v1/organizations/me/logo/ and /api/v1/organizations/me/banner/
"""

import os
from importlib import import_module
from django.urls import reverse
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase
from django.core.files.uploadedfile import SimpleUploadedFile

from accounts.models import User, TenantMembership
from core.models import Tenant
from accounts.constants import AccountStatus, MembershipRole


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

    def tearDown(self):
        # Cleanup any uploaded files
        try:
            if self.tenant.banner:
                self.tenant.banner.delete(save=False)
            if self.tenant.logo:
                self.tenant.logo.delete(save=False)
        except Exception:
            pass

    def test_upload_banner(self):
        url = reverse("organization-banner")
        content = SimpleUploadedFile("banner.jpg", b"\x47\x49\x46\x38\x39\x61", content_type="image/jpeg")
        resp = self.client.post(url, {"banner": content}, format="multipart")

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["success"])

        # Refresh tenant
        self.tenant.refresh_from_db()
        self.assertTrue(bool(self.tenant.banner), "Tenant.banner was not saved")
        # url property should be available when storage configured
        try:
            _ = self.tenant.banner.url
        except Exception:
            # Storage may not provide URL in test environment; ignore
            pass

    def test_upload_logo(self):
        url = reverse("organization-logo")
        content = SimpleUploadedFile("logo.png", b"\x89PNG\r\n\x1a\n", content_type="image/png")
        resp = self.client.post(url, {"logo": content}, format="multipart")

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["success"])

        # Refresh tenant
        self.tenant.refresh_from_db()
        self.assertTrue(bool(self.tenant.logo), "Tenant.logo was not saved")
        try:
            _ = self.tenant.logo.url
        except Exception:
            pass
