"""
BOLAYETU — Player Document, Video, and Achievement Model Tests

Tests for PlayerDocument, PlayerVideo, and PlayerAchievement models.
"""

from django.test import TestCase
from django.utils import timezone
from datetime import date, timedelta
from unittest.mock import Mock

from players.models import Player, PlayerDocument, PlayerVideo, PlayerAchievement
from clubs.models import Club
from competitions.models import Competition
from core.models import Tenant


class PlayerDocumentModelTestCase(TestCase):
    """Test PlayerDocument model."""
    
    def setUp(self):
        """Set up test data."""
        self.tenant = Tenant.objects.create(
            name="Test Organization",
            slug="test-org",
            type="club",
        )
        self.player = Player.objects.create(
            first_name="João",
            last_name="Silva",
            slug="joao-silva",
            nationality="AO",
            primary_position="ST",
        )
        self.club = Club.objects.create(
            name="Test Club",
            slug="test-club",
            tenant=self.tenant,
        )
        # Create mock asset
        self.mock_asset = Mock()
        self.mock_asset.id = "test-asset-id"
        self.mock_asset.public_url = "https://example.com/document.pdf"
    
    def test_create_player_document(self):
        """Test creating a player document."""
        from media_assets.models import MediaAsset
        
        # Create a real MediaAsset for testing
        asset = MediaAsset.objects.create(
            tenant=self.tenant,
            name="document.pdf",
            original_filename="document.pdf",
            object_key="test/doc.pdf",
            asset_type="document",
            category="document",
            mime_type="application/pdf",
            extension="pdf",
            size_bytes=1024,
        )
        
        document = PlayerDocument.objects.create(
            player=self.player,
            title="Contrato 2025",
            category=PlayerDocument.DocumentCategory.CONTRACT,
            asset=asset,
            valid_from=date(2025, 1, 1),
            valid_until=date(2025, 12, 31),
        )
        
        self.assertEqual(document.title, "Contrato 2025")
        self.assertEqual(document.category, "contract")
        self.assertEqual(document.status, "pending")
        self.assertTrue(document.is_private)
    
    def test_document_is_valid(self):
        """Test document validity check."""
        from media_assets.models import MediaAsset
        
        asset = MediaAsset.objects.create(
            tenant=self.tenant,
            name="document.pdf",
            original_filename="document.pdf",
            object_key="test/doc.pdf",
            asset_type="document",
            category="document",
            mime_type="application/pdf",
            extension="pdf",
            size_bytes=1024,
        )
        
        # Test pending document (not valid)
        document = PlayerDocument.objects.create(
            player=self.player,
            title="Test Document",
            category=PlayerDocument.DocumentCategory.OTHER,
            asset=asset,
        )
        self.assertFalse(document.is_valid)
        
        # Test verified document (valid)
        document.status = PlayerDocument.DocumentStatus.VERIFIED
        document.save()
        self.assertTrue(document.is_valid)
        
        # Test expired document
        document.valid_until = date.today() - timedelta(days=1)
        document.save()
        self.assertFalse(document.is_valid)
    
    def test_document_verify(self):
        """Test document verification."""
        from django.contrib.auth import get_user_model
        from media_assets.models import MediaAsset
        
        User = get_user_model()
        user = User.objects.create_user(
            email="admin@test.com",
            password="testpass123",
        )
        
        asset = MediaAsset.objects.create(
            tenant=self.tenant,
            name="document.pdf",
            original_filename="document.pdf",
            object_key="test/doc.pdf",
            asset_type="document",
            category="document",
            mime_type="application/pdf",
            extension="pdf",
            size_bytes=1024,
        )
        
        document = PlayerDocument.objects.create(
            player=self.player,
            title="Test Document",
            category=PlayerDocument.DocumentCategory.OTHER,
            asset=asset,
        )
        
        self.assertEqual(document.status, "pending")
        self.assertIsNone(document.verified_by)
        self.assertIsNone(document.verified_at)
        
        document.verify(user)
        
        self.assertEqual(document.status, "verified")
        self.assertEqual(document.verified_by, user)
        self.assertIsNotNone(document.verified_at)


class PlayerVideoModelTestCase(TestCase):
    """Test PlayerVideo model."""
    
    def setUp(self):
        """Set up test data."""
        self.tenant = Tenant.objects.create(
            name="Test Organization",
            slug="test-org",
            type="club",
        )
        self.player = Player.objects.create(
            first_name="João",
            last_name="Silva",
            slug="joao-silva",
            nationality="AO",
            primary_position="ST",
        )
    
    def test_create_player_video_with_url(self):
        """Test creating a player video with external URL."""
        video = PlayerVideo.objects.create(
            player=self.player,
            title="Golo frente ao Petro - Girabola 2025",
            video_type=PlayerVideo.VideoType.HIGHLIGHTS,
            video_url="https://youtube.com/watch?v=test123",
            thumbnail_url="https://img.youtube.com/vi/test123/0.jpg",
        )
        
        self.assertEqual(video.title, "Golo frente ao Petro - Girabola 2025")
        self.assertEqual(video.video_type, "highlights")
        self.assertEqual(video.status, "published")
        self.assertEqual(video.url, "https://youtube.com/watch?v=test123")
    
    def test_video_thumbnail_property(self):
        """Test video thumbnail property."""
        video = PlayerVideo.objects.create(
            player=self.player,
            title="Test Video",
            video_type=PlayerVideo.VideoType.SKILLS,
            video_url="https://youtube.com/watch?v=test123",
            thumbnail_url="https://example.com/thumb.jpg",
        )
        
        self.assertEqual(video.thumbnail, "https://example.com/thumb.jpg")


class PlayerAchievementModelTestCase(TestCase):
    """Test PlayerAchievement model."""
    
    def setUp(self):
        """Set up test data."""
        self.tenant = Tenant.objects.create(
            name="Test Federation",
            slug="test-fed",
            type="federation",
        )
        self.player = Player.objects.create(
            first_name="João",
            last_name="Silva",
            slug="joao-silva",
            nationality="AO",
            primary_position="ST",
        )
        self.club = Club.objects.create(
            name="Petro de Luanda",
            slug="petro-luanda",
            tenant=self.tenant,
        )
        self.competition = Competition.objects.create(
            name="Girabola 2025",
            tenant=self.tenant,
        )
    
    def test_create_player_achievement(self):
        """Test creating a player achievement."""
        achievement = PlayerAchievement.objects.create(
            player=self.player,
            title="Campeão da Girabola 2025",
            achievement_type=PlayerAchievement.AchievementType.LEAGUE_TITLE,
            level=PlayerAchievement.AchievementLevel.NATIONAL,
            date_achieved=date(2025, 5, 15),
            season="2024/2025",
            club=self.club,
            competition=self.competition,
        )
        
        self.assertEqual(achievement.title, "Campeão da Girabola 2025")
        self.assertEqual(achievement.achievement_type, "league_title")
        self.assertEqual(achievement.level, "national")
        self.assertFalse(achievement.is_verified)
    
    def test_achievement_year_property(self):
        """Test achievement year property."""
        # With date_achieved
        achievement = PlayerAchievement.objects.create(
            player=self.player,
            title="Test Achievement",
            achievement_type=PlayerAchievement.AchievementType.OTHER,
            date_achieved=date(2025, 5, 15),
        )
        self.assertEqual(achievement.year, 2025)
        
        # With season only
        achievement2 = PlayerAchievement.objects.create(
            player=self.player,
            title="Test Achievement 2",
            achievement_type=PlayerAchievement.AchievementType.OTHER,
            season="2023/2024",
        )
        self.assertEqual(achievement2.year, 2023)
    
    def test_achievement_types(self):
        """Test different achievement types."""
        # Individual award
        individual = PlayerAchievement.objects.create(
            player=self.player,
            title="Melhor Marcador 2025",
            achievement_type=PlayerAchievement.AchievementType.TOP_SCORER,
            level=PlayerAchievement.AchievementLevel.NATIONAL,
            stats_snapshot={"goals": 25, "matches": 30},
        )
        self.assertEqual(individual.achievement_type, "top_scorer")
        self.assertEqual(individual.stats_snapshot["goals"], 25)
        
        # International honor
        international = PlayerAchievement.objects.create(
            player=self.player,
            title="Copa das Nações Africanas 2023",
            achievement_type=PlayerAchievement.AchievementType.CONTINENTAL_CUP,
            level=PlayerAchievement.AchievementLevel.CONTINENTAL,
        )
        self.assertEqual(international.level, "continental")
