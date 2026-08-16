from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from players.models import Player, PlayerAchievement, PlayerIdentityDocument, PlayerVideo


User = get_user_model()


class PrivatePlayerContentVisibilityTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="linked-player",
            email="linked-player@test.com",
            password="pass1234",
        )
        self.player = Player.objects.create(
            first_name="Linked",
            last_name="Player",
            slug="linked-player",
            date_of_birth=date(2000, 1, 1),
            nationality="AO",
            primary_position="st",
            status="active",
            is_public=False,
            user=self.user,
        )
        self.client.force_authenticate(user=self.user)

    def test_list_documents_for_linked_non_public_player(self):
        response = self.client.get(f"/api/v1/players/{self.player.slug}/documents/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_videos_for_linked_non_public_player(self):
        response = self.client.get(f"/api/v1/players/{self.player.slug}/videos/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_achievements_for_linked_non_public_player(self):
        response = self.client.get(f"/api/v1/players/{self.player.slug}/achievements/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_identity_documents_for_linked_non_public_player(self):
        response = self.client.get(f"/api/v1/players/{self.player.slug}/identity-documents/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_identity_document_for_linked_non_public_player(self):
        doc = PlayerIdentityDocument.objects.create(
            player=self.player,
            document_type="national_id",
            document_number="AO-123456",
        )

        response = self.client.get(f"/api/v1/players/{self.player.slug}/identity-documents/{doc.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_video_detail_for_linked_non_public_player(self):
        video = PlayerVideo.objects.create(
            player=self.player,
            title="Training Clip",
            video_type=PlayerVideo.VideoType.TRAINING,
            video_url="https://example.com/video.mp4",
            status=PlayerVideo.VideoStatus.DRAFT,
        )

        response = self.client.get(f"/api/v1/players/{self.player.slug}/videos/{video.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_achievement_detail_for_linked_non_public_player(self):
        achievement = PlayerAchievement.objects.create(
            player=self.player,
            title="Season Award",
            achievement_type=PlayerAchievement.AchievementType.BEST_PLAYER,
            level=PlayerAchievement.AchievementLevel.CLUB,
        )

        response = self.client.get(f"/api/v1/players/{self.player.slug}/achievements/{achievement.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
