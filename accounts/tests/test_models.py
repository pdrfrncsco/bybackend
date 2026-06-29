"""
BOLAYETU — User and TenantMembership Model Tests
"""

from django.test import TestCase
from django.db.utils import IntegrityError

from accounts.models import User, TenantMembership
from accounts.constants import AccountStatus, MembershipRole
from core.models import Tenant


class UserModelTest(TestCase):
    """Tests User model properties and methods."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@bolayetu.com",
            password="SecurePass123!",
            first_name="Pedro",
            last_name="Francisco",
        )

    def test_user_creation_default_status(self):
        """User should be created with pending_verification status by default."""
        self.assertEqual(self.user.status, AccountStatus.PENDING_VERIFICATION)
        self.assertFalse(self.user.is_email_verified)

    def test_user_fullname_property(self):
        """User full_name property should format first and last name correctly."""
        self.assertEqual(self.user.full_name, "Pedro Francisco")

    def test_user_fullname_fallback(self):
        """User full_name property should fallback to email prefix if no name exists."""
        user_no_name = User.objects.create_user(
            email="maria@bolayetu.com",
            password="SecurePass123!"
        )
        self.assertEqual(user_no_name.full_name, "maria")

    def test_user_activation(self):
        """activate() should update status to active and verify email."""
        self.user.activate()
        self.assertEqual(self.user.status, AccountStatus.ACTIVE)
        self.assertTrue(self.user.is_email_verified)
        self.assertTrue(self.user.is_active_account)

    def test_user_suspension(self):
        """suspend() should update status to suspended."""
        self.user.suspend()
        self.assertEqual(self.user.status, AccountStatus.SUSPENDED)
        self.assertTrue(self.user.is_suspended)


class TenantMembershipModelTest(TestCase):
    """Tests TenantMembership relationship and methods."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="member@bolayetu.com",
            password="SecurePass123!"
        )
        self.tenant = Tenant.objects.create(
            name="FAF",
            subdomain="faf"
        )
        self.membership = TenantMembership.objects.create(
            user=self.user,
            tenant=self.tenant,
            role=MembershipRole.MEMBER
        )

    def test_membership_creation(self):
        """Membership is created active by default with Member role."""
        self.assertEqual(self.membership.role, MembershipRole.MEMBER)
        self.assertTrue(self.membership.is_active)
        self.assertFalse(self.membership.is_admin)

    def test_membership_promote_admin(self):
        """promote() updates role and correctly reflects admin status."""
        self.membership.promote(MembershipRole.ADMIN)
        self.assertEqual(self.membership.role, MembershipRole.ADMIN)
        self.assertTrue(self.membership.is_admin)

    def test_membership_deactivate(self):
        """deactivate() sets is_active to False."""
        self.membership.deactivate()
        self.assertFalse(self.membership.is_active)

    def test_unique_user_tenant_membership(self):
        """User cannot have multiple membership records in the same Tenant."""
        with self.assertRaises(IntegrityError):
            TenantMembership.objects.create(
                user=self.user,
                tenant=self.tenant,
                role=MembershipRole.OWNER
            )
