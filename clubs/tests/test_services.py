"""
BOLAYETU — Club Service Tests

Tests ClubService methods for club management, member management.
"""

from django.test import TestCase

from accounts.models import User
from accounts.constants import AccountStatus
from core.models import Tenant
from clubs.models import Club, ClubMember
from clubs.constants import ClubStatus, ClubMemberRole
from clubs.services import ClubService
from clubs.exceptions import (
    DuplicateClubName,
    DuplicateJerseyNumber,
    DuplicateClubMember,
)


class ClubServiceCreateTest(TestCase):
    """Tests ClubService.create_club()"""

    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Org")

    def test_create_club_success(self):
        """Should create a club successfully."""
        club = ClubService.create_club(
            tenant=self.tenant,
            name="FC Porto",
            short_name="FCP",
            founded_year=1893,
        )
        self.assertEqual(club.name, "FC Porto")
        self.assertEqual(club.short_name, "FCP")
        self.assertEqual(club.founded_year, 1893)

    def test_create_club_duplicate_name(self):
        """Should raise DuplicateClubName if name already exists in tenant."""
        ClubService.create_club(tenant=self.tenant, name="Benfica")
        
        with self.assertRaises(DuplicateClubName):
            ClubService.create_club(tenant=self.tenant, name="Benfica")

    def test_create_club_same_name_different_tenant(self):
        """Should allow same name in different tenant."""
        tenant2 = Tenant.objects.create(name="Another Org")
        
        club1 = ClubService.create_club(tenant=self.tenant, name="Sporting")
        club2 = ClubService.create_club(tenant=tenant2, name="Sporting")
        
        self.assertEqual(club1.name, club2.name)
        self.assertNotEqual(club1.id, club2.id)


class ClubServiceUpdateTest(TestCase):
    """Tests ClubService.update_club()"""

    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Org")
        self.club = ClubService.create_club(
            tenant=self.tenant,
            name="Original Name",
            short_name="ON",
        )

    def test_update_club_partial(self):
        """Should update only specified fields."""
        updated = ClubService.update_club(
            club=self.club,
            name="Updated Name",
        )
        self.assertEqual(updated.name, "Updated Name")
        self.assertEqual(updated.short_name, "ON")

    def test_update_club_multiple_fields(self):
        """Should update multiple fields."""
        updated = ClubService.update_club(
            club=self.club,
            name="New Name",
            short_name="NN",
            founded_year=2000,
            city="Lisbon",
        )
        self.assertEqual(updated.name, "New Name")
        self.assertEqual(updated.short_name, "NN")
        self.assertEqual(updated.founded_year, 2000)


class ClubServiceStatusTest(TestCase):
    """Tests ClubService activate/suspend methods"""

    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Org")
        self.club = ClubService.create_club(tenant=self.tenant, name="Test Club")

    def test_activate_club(self):
        """Should activate a club."""
        activated = ClubService.activate(club=self.club)
        self.assertEqual(activated.status, ClubStatus.ACTIVE)

    def test_suspend_club(self):
        """Should suspend a club."""
        suspended = ClubService.suspend(club=self.club)
        self.assertEqual(suspended.status, ClubStatus.SUSPENDED)


class ClubMemberServiceTest(TestCase):
    """Tests ClubService member management methods"""

    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Org")
        self.club = ClubService.create_club(tenant=self.tenant, name="Test Club")
        self.user = User.objects.create_user(
            email="player@bolayetu.com",
            password="Pass123!",
            status=AccountStatus.ACTIVE,
        )

    def test_add_member_success(self):
        """Should add a member to the club."""
        member = ClubService.add_member(
            club=self.club,
            user=self.user,
            full_name="João Silva",
            role=ClubMemberRole.PLAYER,
            jersey_number=10,
            position="Forward",
        )
        self.assertEqual(member.user, self.user)
        self.assertEqual(member.role, ClubMemberRole.PLAYER)
        self.assertTrue(member.is_active)

    def test_add_member_duplicate(self):
        """Should raise DuplicateClubMember if already active member."""
        ClubService.add_member(
            club=self.club,
            user=self.user,
            role=ClubMemberRole.PLAYER,
        )
        
        with self.assertRaises(DuplicateClubMember):
            ClubService.add_member(
                club=self.club,
                user=self.user,
                role=ClubMemberRole.PLAYER,
            )

    def test_add_member_duplicate_jersey(self):
        """Should raise DuplicateJerseyNumber if jersey in use."""
        ClubService.add_member(
            club=self.club,
            user=self.user,
            jersey_number=10,
            role=ClubMemberRole.PLAYER,
        )
        
        user2 = User.objects.create_user(
            email="another@bolayetu.com",
            password="Pass123!",
        )
        
        with self.assertRaises(DuplicateJerseyNumber):
            ClubService.add_member(
                club=self.club,
                user=user2,
                jersey_number=10,
                role=ClubMemberRole.PLAYER,
            )

    def test_update_member(self):
        """Should update member details."""
        member = ClubService.add_member(
            club=self.club,
            user=self.user,
            jersey_number=10,
        )
        
        updated = ClubService.update_member(
            member=member,
            jersey_number=7,
            position="Midfielder",
        )
        self.assertEqual(updated.jersey_number, 7)
        self.assertEqual(updated.position, "Midfielder")

    def test_remove_member(self):
        """Should deactivate a member."""
        member = ClubService.add_member(club=self.club, user=self.user)
        self.assertTrue(member.is_active)
        
        ClubService.remove_member(member=member)
        
        member.refresh_from_db()
        self.assertFalse(member.is_active)
