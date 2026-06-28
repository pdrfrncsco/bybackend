"""
BOLAYETU — Accounts Permission Tests
"""

from unittest.mock import Mock
from django.test import TestCase

from accounts.permissions import IsActiveAccount, IsAccountOwner, IsPlatformAdmin
from accounts.models import User
from accounts.constants import AccountStatus


class PermissionsTest(TestCase):
    """Tests custom DRF permissions against mock request/views."""

    def setUp(self):
        self.active_user = User.objects.create_user(
            email="active@bolayetu.com",
            password="SecurePass123!",
            status=AccountStatus.ACTIVE,
        )
        self.pending_user = User.objects.create_user(
            email="pending@bolayetu.com",
            password="SecurePass123!",
            status=AccountStatus.PENDING_VERIFICATION,
        )
        self.admin_user = User.objects.create_user(
            email="admin@bolayetu.com",
            password="SecurePass123!",
            is_superuser=True,
        )

    def test_is_active_account(self):
        """IsActiveAccount allows active users and blocks pending/unauthenticated users."""
        permission = IsActiveAccount()

        # Active user should pass
        request = Mock(user=self.active_user)
        self.assertTrue(permission.has_permission(request, None))

        # Pending user should fail
        request = Mock(user=self.pending_user)
        self.assertFalse(permission.has_permission(request, None))

        # Anonymous/unauthenticated user should fail
        anonymous_user = Mock(is_authenticated=False)
        request = Mock(user=anonymous_user)
        self.assertFalse(permission.has_permission(request, None))

    def test_is_account_owner(self):
        """IsAccountOwner allows access only to user matching the target object."""
        permission = IsAccountOwner()

        # Same user should pass
        request = Mock(user=self.active_user)
        self.assertTrue(permission.has_object_permission(request, None, self.active_user))

        # Different user should fail
        self.assertFalse(permission.has_object_permission(request, None, self.pending_user))

    def test_is_platform_admin(self):
        """IsPlatformAdmin allows superusers only."""
        permission = IsPlatformAdmin()

        # Superuser should pass
        request = Mock(user=self.admin_user)
        self.assertTrue(permission.has_permission(request, None))

        # Regular user should fail
        request = Mock(user=self.active_user)
        self.assertFalse(permission.has_permission(request, None))
