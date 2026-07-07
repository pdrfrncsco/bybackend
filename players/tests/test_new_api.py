"""
BOLAYETU — Player Document, Video, and Achievement API Tests

Tests for PlayerDocument, PlayerVideo, and PlayerAchievement API endpoints.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from datetime import date, timedelta

from players.models import Player, PlayerDocument, PlayerVideo, PlayerAchievement
from clubs.models import Club
from core.models import Tenant
from accounts.models import TenantMembership


class PlayerDocumentAPITestCase(TestCase):
    """Test PlayerDocument API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create tenant
        self.tenant = Tenant.objects.create(
            name="Test Organization",
            slug="test-org",
            type="club",
        )
        
        # Create users
        User = get_user_model()
        self.admin_user = User.objects.create_user(
            email="admin@test.com",
            password="testpass123",
            first_name="Admin",
            last_name="User",
            is_staff=True,
        )
        TenantMembership.objects.create(
            user=self.admin_user,
            tenant=self.tenant,
            role="admin",
        )
        
        self.normal_user = User.objects.create_user(
            email="user@test.com",
            password="testpass123",
            first_name="Normal",
            last_name="User",
        )
        
        # Create player
        self.player = Player.objects.create(
            first_name="João",
            last_name="Silva",
            slug="joao-silva",
            nationality="AO",
            primary_position="ST",
        )
    
    def test_list_player_documents_public(self):
        """Test listing player documents as public user."""
        response = self.client.get(f"/api/v1/players/{self.player.slug}/documents/")
        self.assertEqual(response.status_code, 200)
    
    def test_upload_document_requires_auth(self):
        """Test that uploading document requires authentication."""
        response = self.client.post(
            f"/api/v1/players/{self.player.slug}/documents/",
            {"title": "Test Document"},
        )
        self.assertEqual(response.status_code, 401)


class PlayerVideoAPITestCase(TestCase):
    """Test PlayerVideo API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create tenant
        self.tenant = Tenant.objects.create(
            name="Test Organization",
            slug="test-org",
            type="club",
        )
        
        # Create users
        User = get_user_model()
        self.admin_user = User.objects.create_user(
            email="admin@test.com",
            password="testpass123",
            first_name="Admin",
            last_name="User",
            is_staff=True,
        )
        TenantMembership.objects.create(
            user=self.admin_user,
            tenant=self.tenant,
            role="admin",
        )
        
        # Create player
        self.player = Player.objects.create(
            first_name="João",
            last_name="Silva",
            slug="joao-silva",
            nationality="AO",
            primary_position="ST",
        )
    
    def test_list_player_videos_public(self):
        """Test listing player videos as public user."""
        response = self.client.get(f"/api/v1/players/{self.player.slug}/videos/")
        self.assertEqual(response.status_code, 200)
    
    def test_upload_video_requires_auth(self):
        """Test that uploading video requires authentication."""
        response = self.client.post(
            f"/api/v1/players/{self.player.slug}/videos/",
            {"title": "Test Video"},
        )
        self.assertEqual(response.status_code, 401)
    
    def test_list_only_published_videos(self):
        """Test that only published videos are shown to public users."""
        # Create a draft video
        draft = PlayerVideo.objects.create(
            player=self.player,
            title="Draft Video",
            video_type=PlayerVideo.VideoType.HIGHLIGHTS,
            video_url="https://youtube.com/watch?v=draft",
            status=PlayerVideo.VideoStatus.DRAFT,
        )
        
        # Create a published video
        published = PlayerVideo.objects.create(
            player=self.player,
            title="Published Video",
            video_type=PlayerVideo.VideoType.HIGHLIGHTS,
            video_url="https://youtube.com/watch?v=published",
            status=PlayerVideo.VideoStatus.PUBLISHED,
        )
        
        response = self.client.get(f"/api/v1/players/{self.player.slug}/videos/")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        results = data.get("data", {}).get("results", data.get("results", []))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Published Video")


class PlayerAchievementAPITestCase(TestCase):
    """Test PlayerAchievement API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create tenant
        self.tenant = Tenant.objects.create(
            name="Test Federation",
            slug="test-fed",
            type="federation",
        )
        
        # Create users
        User = get_user_model()
        self.admin_user = User.objects.create_user(
            email="admin@test.com",
            password="testpass123",
            first_name="Admin",
            last_name="User",
            is_staff=True,
        )
        TenantMembership.objects.create(
            user=self.admin_user,
            tenant=self.tenant,
            role="admin",
        )
        
        # Create player
        self.player = Player.objects.create(
            first_name="João",
            last_name="Silva",
            slug="joao-silva",
            nationality="AO",
            primary_position="ST",
        )
        
        # Create club
        self.club = Club.objects.create(
            name="Petro de Luanda",
            slug="petro-luanda",
            tenant=self.tenant,
        )
    
    def test_list_player_achievements_public(self):
        """Test listing player achievements as public user."""
        response = self.client.get(f"/api/v1/players/{self.player.slug}/achievements/")
        self.assertEqual(response.status_code, 200)
    
    def test_add_achievement_requires_auth(self):
        """Test that adding achievement requires authentication."""
        response = self.client.post(
            f"/api/v1/players/{self.player.slug}/achievements/",
            {
                "title": "Test Achievement",
                "achievement_type": "league_title",
                "level": "national",
            },
        )
        self.assertEqual(response.status_code, 401)
    
    def test_filter_achievements_by_type(self):
        """Test filtering achievements by type."""
        # Create achievements of different types
        PlayerAchievement.objects.create(
            player=self.player,
            title="League Title",
            achievement_type=PlayerAchievement.AchievementType.LEAGUE_TITLE,
            level=PlayerAchievement.AchievementLevel.NATIONAL,
        )
        PlayerAchievement.objects.create(
            player=self.player,
            title="Top Scorer",
            achievement_type=PlayerAchievement.AchievementType.TOP_SCORER,
            level=PlayerAchievement.AchievementLevel.NATIONAL,
        )
        
        response = self.client.get(
            f"/api/v1/players/{self.player.slug}/achievements/?type=league_title"
        )
        self.assertEqual(response.status_code, 200)


class PlayerDetailWithRelatedDataTestCase(TestCase):
    """Test PlayerDetailSerializer with videos, documents, and achievements."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create tenant
        self.tenant = Tenant.objects.create(
            name="Test Organization",
            slug="test-org",
            type="club",
        )
        
        # Create player
        self.player = Player.objects.create(
            first_name="João",
            last_name="Silva",
            slug="joao-silva",
            nationality="AO",
            primary_position="ST",
            total_matches=50,
            total_goals=25,
            total_assists=10,
        )
        
        # Create related data
        PlayerVideo.objects.create(
            player=self.player,
            title="Highlights 2025",
            video_type=PlayerVideo.VideoType.HIGHLIGHTS,
            video_url="https://youtube.com/watch?v=test",
            status=PlayerVideo.VideoStatus.PUBLISHED,
        )
        
        PlayerAchievement.objects.create(
            player=self.player,
            title="Campeão Nacional",
            achievement_type=PlayerAchievement.AchievementType.LEAGUE_TITLE,
            level=PlayerAchievement.AchievementLevel.NATIONAL,
            date_achieved=date(2025, 5, 15),
        )
    
    def test_player_detail_includes_videos(self):
        """Test that player detail includes videos."""
        response = self.client.get(f"/api/v1/players/{self.player.slug}/")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("videos", data["data"])
        self.assertEqual(len(data["data"]["videos"]), 1)
        self.assertEqual(data["data"]["videos"][0]["title"], "Highlights 2025")
    
    def test_player_detail_includes_achievements(self):
        """Test that player detail includes achievements."""
        response = self.client.get(f"/api/v1/players/{self.player.slug}/")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("achievements", data["data"])
        self.assertEqual(len(data["data"]["achievements"]), 1)
        self.assertEqual(data["data"]["achievements"][0]["title"], "Campeão Nacional")
