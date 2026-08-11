"""
BOLAYETU — Player Selector Tests

Tests for PlayerSelector read queries.
"""

from django.test import TestCase
from datetime import date

from players.models import Player, PlayerRegistration
from players.selectors import PlayerSelector, PlayerRegistrationSelector
from clubs.models import Club
from competitions.models import Competition
from core.models import Tenant


class PlayerSelectorTestCase(TestCase):
    """Test PlayerSelector queries."""
    
    def setUp(self):
        self.player1 = Player.objects.create(
            first_name="John",
            last_name="Doe",
            slug="john-doe",
            date_of_birth=date(2000, 1, 15),
            nationality="PT",
            primary_position="ST",
            status="active"
        )
        
        self.player2 = Player.objects.create(
            first_name="Maria",
            last_name="Silva",
            slug="maria-silva",
            date_of_birth=date(1998, 5, 20),
            nationality="BR",
            primary_position="GK",
            status="active"
        )
        
        self.player3 = Player.objects.create(
            first_name="Inactive",
            last_name="Player",
            slug="inactive-player",
            date_of_birth=date(2002, 3, 10),
            nationality="PT",
            primary_position="MF",
            status="retired"
        )
    
    def test_get_by_id(self):
        """Test get_by_id selector."""
        player = PlayerSelector.get_by_id(self.player1.id)
        self.assertEqual(player.slug, "john-doe")
    
    def test_get_by_id_not_found(self):
        """Test get_by_id returns None for nonexistent player."""
        player = PlayerSelector.get_by_id(99999)
        self.assertIsNone(player)
    
    def test_get_by_slug(self):
        """Test get_by_slug selector."""
        player = PlayerSelector.get_by_slug("john-doe")
        self.assertEqual(player.id, self.player1.id)
    
    def test_get_by_slug_not_found(self):
        """Test get_by_slug returns None for nonexistent slug."""
        player = PlayerSelector.get_by_slug("nonexistent")
        self.assertIsNone(player)
    
    def test_list_active(self):
        """Test list_active returns only active players."""
        players = PlayerSelector.list_active()
        
        self.assertEqual(players.count(), 2)
        slugs = [p.slug for p in players]
        self.assertIn("john-doe", slugs)
        self.assertIn("maria-silva", slugs)
        self.assertNotIn("inactive-player", slugs)
    
    def test_search(self):
        """Test search by name."""
        players = PlayerSelector.search("maria")
        
        self.assertEqual(players.count(), 1)
        self.assertEqual(players.first().slug, "maria-silva")
    
    def test_search_case_insensitive(self):
        """Test search is case insensitive."""
        players = PlayerSelector.search("JOHN")
        
        self.assertEqual(players.count(), 1)
        self.assertEqual(players.first().slug, "john-doe")
    
    def test_list_by_position(self):
        """Test list_by_position."""
        players = PlayerSelector.list_by_position("ST")
        
        self.assertEqual(players.count(), 1)
        self.assertEqual(players.first().slug, "john-doe")
    
    def test_list_by_nationality(self):
        """Test list_by_nationality."""
        players = PlayerSelector.list_by_nationality("PT")
        
        self.assertEqual(players.count(), 1)
        self.assertEqual(players.first().slug, "john-doe")


class PlayerRegistrationSelectorTestCase(TestCase):
    """Test PlayerRegistrationSelector queries."""
    
    def setUp(self):
        self.tenant = Tenant.objects.create(
            name="Test Org",
            slug="test-org"
        )
        
        self.club1 = Club.objects.create(
            name="Test Club 1",
            slug="test-club-1",
            tenant=self.tenant
        )
        
        self.club2 = Club.objects.create(
            name="Test Club 2",
            slug="test-club-2",
            tenant=self.tenant
        )
        
        self.competition = Competition.objects.create(
            name="Test League",
            slug="test-league",
            tenant=self.tenant
        )
        
        self.player1 = Player.objects.create(
            first_name="John",
            last_name="Doe",
            slug="john-doe",
            date_of_birth=date(2000, 1, 15),
            nationality="PT",
            primary_position="ST"
        )
        
        self.player2 = Player.objects.create(
            first_name="Maria",
            last_name="Silva",
            slug="maria-silva",
            date_of_birth=date(1998, 5, 20),
            nationality="BR",
            primary_position="GK"
        )
        
        # Current registration
        self.reg1 = PlayerRegistration.objects.create(
            player=self.player1,
            club=self.club1,
            competition=self.competition,
            tenant=self.tenant,
            shirt_number=10,
            joined_date=date(2022, 1, 1),
            status="registered"
        )
        
        # Transferred registration
        self.reg2 = PlayerRegistration.objects.create(
            player=self.player1,
            club=self.club2,
            competition=self.competition,
            tenant=self.tenant,
            shirt_number=15,
            joined_date=date(2023, 1, 1),
            left_date=date(2024, 1, 1),
            status="transferred"
        )
        
        # Another player's registration
        self.reg3 = PlayerRegistration.objects.create(
            player=self.player2,
            club=self.club1,
            competition=self.competition,
            tenant=self.tenant,
            shirt_number=1,
            joined_date=date(2020, 1, 1),
            status="registered"
        )
    
    def test_get_current_registration(self):
        """Test get_current_registration."""
        reg = PlayerRegistrationSelector.get_current_registration(self.player1.id)
        
        self.assertEqual(reg.id, self.reg1.id)
        self.assertEqual(reg.status, "registered")
    
    def test_list_by_club(self):
        """Test list_by_club."""
        registrations = PlayerRegistrationSelector.list_by_club(self.club1.id)
        
        self.assertEqual(registrations.count(), 2)
        ids = [r.id for r in registrations]
        self.assertIn(self.reg1.id, ids)
        self.assertIn(self.reg3.id, ids)
    
    def test_list_by_competition(self):
        """Test list_by_competition."""
        registrations = PlayerRegistrationSelector.list_by_competition(self.competition.id)
        
        # Should only include "registered" status
        self.assertEqual(registrations.count(), 2)
        statuses = [r.status for r in registrations]
        self.assertNotIn("transferred", statuses)
    
    def test_list_career(self):
        """Test list_career includes all registrations."""
        career = PlayerRegistrationSelector.list_career(self.player1.id)
        
        self.assertEqual(career.count(), 2)
        ids = [r.id for r in career]
        self.assertIn(self.reg1.id, ids)
        self.assertIn(self.reg2.id, ids)


class PlayerSelectorsAdditionalTestCase(TestCase):
    """Additional tests for new selectors: global_id, profile_photo, invites, career/statistics selectors."""

    def setUp(self):
        from media_assets.models.media_asset import MediaAsset
        from players.models import PlayerInvite, PlayerCareer, PlayerSeasonStatistics
        from clubs.models import Club
        from core.models import Tenant
        from competitions.models import Competition

        self.tenant = Tenant.objects.create(name="Extra Tenant", slug="extra-tenant")
        self.club = Club.objects.create(name="Extra Club", slug="extra-club", tenant=self.tenant)
        self.competition = Competition.objects.create(name="Cup", slug="cup", tenant=self.tenant)

        self.player = Player.objects.create(
            first_name="Global",
            last_name="Player",
            slug="global-player",
            date_of_birth=date(1995, 6, 1),
            nationality="PT",
            primary_position="cm",
            status=Player.PlayerStatus.ACTIVE,
        )

        # Create a MediaAsset to attach as profile_photo
        self.asset = MediaAsset.objects.create(
            name="avatar.jpg",
            original_filename="avatar.jpg",
            mime_type="image/jpeg",
            extension="jpg",
            size_bytes=12345,
            object_key="avatars/avatar.jpg",
            cdn_url="https://cdn.example/avatar.jpg",
        )
        self.player.profile_photo = self.asset
        self.player.save()

        # Invite
        self.invite = PlayerInvite.objects.create(email="invitee@example.com", first_name="Inv", last_name="It", invited_by=None, club=self.club)

        # Career entry
        self.career = PlayerCareer.objects.create(player=self.player, club=self.club, season="2024", competition=self.competition, appearances=5, goals=1)

        # Season statistics
        self.stats = PlayerSeasonStatistics.objects.create(player=self.player, season="2024", club=self.club, competition=self.competition, appearances=5, goals=1)

    def test_get_by_global_id(self):
        # global_id is auto-generated on save
        pid = self.player.global_id
        self.assertIsNotNone(pid)
        p = PlayerSelector.get_by_global_id(pid)
        self.assertIsNotNone(p)
        self.assertEqual(p.id, self.player.id)

    def test_get_with_profile_photo(self):
        p = PlayerSelector.get_with_profile_photo(self.player.id, prefetch_related=True)
        self.assertIsNotNone(p.profile_photo)
        self.assertEqual(p.profile_photo.id, self.asset.id)

    def test_invite_selectors(self):
        from players.selectors import PlayerInviteSelector
        found = PlayerInviteSelector.get_by_token(self.invite.token)
        self.assertIsNotNone(found)
        self.assertEqual(found.id, self.invite.id)
        lst = PlayerInviteSelector.list_by_club(self.club.id)
        self.assertTrue(lst.filter(id=self.invite.id).exists())

    def test_career_selector(self):
        from players.selectors import PlayerCareerSelector
        entries = PlayerCareerSelector.list_for_player(self.player.id)
        self.assertTrue(entries.filter(id=self.career.id).exists())

    def test_season_statistics_selector(self):
        from players.selectors import PlayerSeasonStatisticsSelector
        rows = PlayerSeasonStatisticsSelector.get_for_player(self.player.id)
        self.assertTrue(rows.filter(id=self.stats.id).exists())
