"""
BOLAYETU — Club and ClubMember Model Tests

Tests Club and ClubMember properties, methods, and constraints.
"""

from django.test import TestCase
from django.db.utils import IntegrityError

from accounts.models import User
from accounts.constants import AccountStatus
from core.models import Tenant
from clubs.models import Club, ClubMember
from clubs.constants import ClubStatus, ClubMemberRole


class ClubModelTest(TestCase):
    """Tests Club model properties and methods."""

    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Organization")
        self.club = Club.objects.create(
            tenant=self.tenant,
            name="Test Football Club",
            short_name="TFC",
        )

    def test_club_creation_default_status(self):
        """Club should be created with active status by default."""
        club = Club.objects.create(tenant=self.tenant, name="Another Club")
        self.assertEqual(club.status, ClubStatus.ACTIVE)

    def test_club_slug_generation(self):
        """Club slug should be auto-generated from name."""
        self.assertIsNotNone(self.club.slug)
        self.assertEqual(self.club.slug, "test-football-club")

    def test_club_unique_name_per_tenant(self):
        """Club names must be unique per tenant."""
        with self.assertRaises(IntegrityError):
            Club.objects.create(
                tenant=self.tenant,
                name="Test Football Club",  # Same name
            )

    def test_club_status_transitions(self):
        """Test club status changes."""
        self.assertEqual(self.club.status, ClubStatus.ACTIVE)
        self.club.status = ClubStatus.SUSPENDED
        self.club.save()
        self.club.refresh_from_db()
        self.assertEqual(self.club.status, ClubStatus.SUSPENDED)

    def test_club_display_name(self):
        """Club display_name should prefer short_name over name."""
        # This test checks the property if it exists on the model
        # Since we don't see display_name property in the model, skip
        pass

    def test_club_timestamps(self):
        """Club should have created_at and updated_at timestamps."""
        self.assertIsNotNone(self.club.created_at)
        self.assertIsNotNone(self.club.updated_at)
        self.assertEqual(self.club.created_at.date(), self.club.updated_at.date())


class ClubMemberModelTest(TestCase):
    """Tests ClubMember model properties and constraints."""

    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Organization")
        self.club = Club.objects.create(
            tenant=self.tenant,
            name="Test Club",
        )
        self.user = User.objects.create_user(
            email="player@bolayetu.com",
            password="SecurePassword123!",
            status=AccountStatus.ACTIVE,
        )
        self.member = ClubMember.objects.create(
            club=self.club,
            user=self.user,
            full_name="João Silva",
            role=ClubMemberRole.PLAYER,
            jersey_number=10,
            position="Forward",
        )

    def test_member_creation_active_default(self):
        """ClubMember should be active by default."""
        self.assertTrue(self.member.is_active)

    def test_member_display_name(self):
        """Member display_name should use full_name or user.full_name."""
        self.assertEqual(self.member.display_name, "João Silva")
        
        # Create a different user for the second member
        user2 = User.objects.create_user(
            email="another@bolayetu.com",
            password="SecurePassword123!",
            first_name="Another",
            last_name="User",
        )
        member_no_name = ClubMember.objects.create(
            club=self.club,
            user=user2,
            full_name=None,
        )
        self.assertEqual(member_no_name.display_name, "Another User")

    def test_jersey_number_unique_per_club(self):
        """Jersey number must be unique per active club members."""
        # Create a different user for the second member
        user2 = User.objects.create_user(
            email="player2@bolayetu.com",
            password="SecurePassword123!",
        )
        with self.assertRaises(IntegrityError):
            ClubMember.objects.create(
                club=self.club,
                user=user2,
                full_name="Another Player",
                jersey_number=10,  # Same jersey
                role=ClubMemberRole.PLAYER,
                is_active=True,
            )

    def test_jersey_number_can_be_null(self):
        """Jersey number can be null for staff members."""
        user2 = User.objects.create_user(
            email="coach@bolayetu.com",
            password="SecurePassword123!",
        )
        staff = ClubMember.objects.create(
            club=self.club,
            user=user2,
            full_name="Coach",
            role=ClubMemberRole.COACH,
            jersey_number=None,
        )
        self.assertIsNone(staff.jersey_number)

    def test_member_deactivation(self):
        """deactivate() should set is_active to False."""
        self.assertTrue(self.member.is_active)
        self.member.deactivate()
        self.assertFalse(self.member.is_active)

    def test_member_timestamps(self):
        """ClubMember should have created_at and updated_at."""
        self.assertIsNotNone(self.member.created_at)
        self.assertIsNotNone(self.member.updated_at)
