"""
BOLAYETU — User and TenantMembership Selector Tests
"""

from django.test import TestCase

from accounts.selectors import UserSelector, TenantMembershipSelector
from accounts.models import User, TenantMembership
from accounts.constants import AccountStatus, MembershipRole
from core.models import Tenant


class UserSelectorTest(TestCase):
    """Tests read-only query selectors for User."""

    def setUp(self):
        self.user1 = User.objects.create_user(
            email="user1@bolayetu.com",
            password="SecurePass123!",
            first_name="Primeiro",
            status=AccountStatus.ACTIVE,
            is_email_verified=True,
        )
        self.user2 = User.objects.create_user(
            email="user2@bolayetu.com",
            password="SecurePass123!",
            first_name="Segundo",
            status=AccountStatus.PENDING_VERIFICATION,
        )

    def test_get_by_id(self):
        """UserSelector.get_by_id retrieves user by UUID."""
        fetched = UserSelector.get_by_id(user_id=self.user1.id)
        self.assertEqual(fetched, self.user1)

        none_fetched = UserSelector.get_by_id(user_id=self.user2.id)
        self.assertEqual(none_fetched, self.user2)

    def test_get_by_email(self):
        """UserSelector.get_by_email retrieves user by case-insensitive email."""
        fetched = UserSelector.get_by_email(email="USER1@bolayetu.com")
        self.assertEqual(fetched, self.user1)

    def test_email_exists(self):
        """UserSelector.email_exists returns True if registered, case-insensitive."""
        self.assertTrue(UserSelector.email_exists(email="user2@bolayetu.com"))
        self.assertFalse(UserSelector.email_exists(email="nonexistent@bolayetu.com"))

    def test_list_active(self):
        """UserSelector.list_active returns active status users only."""
        active_users = list(UserSelector.list_active())
        self.assertIn(self.user1, active_users)
        self.assertNotIn(self.user2, active_users)


class TenantMembershipSelectorTest(TestCase):
    """Tests read-only query selectors for TenantMembership."""

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
            role=MembershipRole.MEMBER,
            is_active=True
        )

    def test_get_membership(self):
        """TenantMembershipSelector.get_membership retrieves bridge record."""
        membership = TenantMembershipSelector.get_membership(user=self.user, tenant_id=self.tenant.id)
        self.assertEqual(membership, self.membership)

    def test_user_belongs_to_tenant(self):
        """TenantMembershipSelector.user_belongs_to_tenant validates active memberships."""
        self.assertTrue(TenantMembershipSelector.user_belongs_to_tenant(user=self.user, tenant_id=self.tenant.id))

    def test_list_tenant_members(self):
        """TenantMembershipSelector.list_tenant_members returns active members of a tenant."""
        members = list(TenantMembershipSelector.list_tenant_members(tenant_id=self.tenant.id))
        self.assertEqual(len(members), 1)
        self.assertEqual(members[0].user, self.user)
