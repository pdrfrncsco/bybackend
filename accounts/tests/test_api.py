"""
BOLAYETU — Authentication and User API Tests
"""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from accounts.constants import AccountStatus


class AuthAPITest(APITestCase):
    """Tests authentication API endpoints."""

    def test_register_api_success(self):
        """POST /api/v1/auth/register/ creates user and returns tokens in standard format."""
        url = reverse("register")
        data = {
            "email": "api_register@bolayetu.com",
            "password": "SecurePassword123!",
            "password_confirm": "SecurePassword123!",
            "first_name": "API",
            "last_name": "Tester",
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertIn("access", response.data["data"])
        self.assertIn("refresh", response.data["data"])
        self.assertEqual(response.data["data"]["user"]["email"], "api_register@bolayetu.com")

    def test_register_api_password_mismatch(self):
        """POST /api/v1/auth/register/ returns validation error if passwords do not match."""
        url = reverse("register")
        data = {
            "email": "api_mismatch@bolayetu.com",
            "password": "SecurePassword123!",
            "password_confirm": "WrongPassword123!",
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])

    def test_login_api_success(self):
        """POST /api/v1/auth/login/ authenticates user and returns tokens."""
        # Pre-create user (register automatically sets status to active in our test Authservice register flow)
        User.objects.create_user(
            email="api_login@bolayetu.com",
            password="SecurePassword123!",
            status=AccountStatus.ACTIVE,
            is_email_verified=True,
        )

        url = reverse("login")
        data = {
            "email": "api_login@bolayetu.com",
            "password": "SecurePassword123!",
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertIn("access", response.data["data"])

    def test_login_api_invalid_credentials(self):
        """POST /api/v1/auth/login/ returns 401 on incorrect credentials."""
        url = reverse("login")
        data = {
            "email": "api_wrong@bolayetu.com",
            "password": "WrongPassword123!",
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data["success"])


class UserAPITest(APITestCase):
    """Tests profile and user settings endpoints."""

    def setUp(self):
        self.password = "SecurePassword123!"
        self.user = User.objects.create_user(
            email="profile_api@bolayetu.com",
            password=self.password,
            first_name="Original",
            last_name="User",
            status=AccountStatus.ACTIVE,
            is_email_verified=True,
        )
        # Login to get JWT
        login_url = reverse("login")
        response = self.client.post(login_url, {"email": self.user.email, "password": self.password}, format="json")
        self.token = response.data["data"]["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_get_me_api(self):
        """GET /api/v1/auth/me/ returns authenticated user's profile."""
        url = reverse("me")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["email"], self.user.email)
        self.assertEqual(response.data["data"]["first_name"], "Original")

    def test_patch_me_api(self):
        """PATCH /api/v1/auth/me/ updates profile and returns updated serializer."""
        url = reverse("me")
        data = {
            "first_name": "Modificado",
            "phone": "923111222",
        }
        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["first_name"], "Modificado")
        self.assertEqual(response.data["data"]["phone"], "923111222")

    def test_change_password_api(self):
        """POST /api/v1/auth/me/change-password/ changes password successfully."""
        url = reverse("change-password")
        data = {
            "old_password": self.password,
            "new_password": "NewSecurePassword456!",
            "new_password_confirm": "NewSecurePassword456!",
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])

        # Try to login with new password to confirm
        self.client.credentials()  # Clear auth headers
        login_url = reverse("login")
        login_resp = self.client.post(
            login_url,
            {"email": self.user.email, "password": "NewSecurePassword456!"},
            format="json"
        )
        self.assertEqual(login_resp.status_code, status.HTTP_200_OK)
