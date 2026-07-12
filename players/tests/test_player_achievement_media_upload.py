from datetime import date

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from players.models import Player, PlayerAchievement

User = get_user_model()


class PlayerAchievementMediaUploadAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.player_user = User.objects.create_user(
            email="player@test.com",
            password="SecurePass123!",
        )

        self.player = Player.objects.create(
            user=self.player_user,
            first_name="Joao",
            last_name="Silva",
            slug="joao-silva",
            date_of_birth=date(2000, 1, 1),
            nationality="AO",
            primary_position="st",
            status="active",
        )

    def _pdf(self, name="certificate.pdf"):
        return SimpleUploadedFile(name, b"%PDF-1.4 fake", content_type="application/pdf")

    def _png(self, name="trophy.png"):
        return SimpleUploadedFile(name, b"\x89PNG\r\n\x1a\nfake", content_type="image/png")

    def test_player_uploads_achievement_with_trophy_via_dam(self):
        self.client.force_authenticate(user=self.player_user)
        response = self.client.post(
            f"/api/v1/players/{self.player.slug}/achievements/",
            {
                "title": "Campeao Nacional 2026",
                "achievement_type": "league_title",
                "level": "national",
                "trophy_image": self._png("trophy.png"),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertTrue(payload["data"]["trophy_image"])
        self.assertEqual(PlayerAchievement.objects.filter(player=self.player).count(), 1)

    def test_player_uploads_achievement_with_certificate_via_dam(self):
        self.client.force_authenticate(user=self.player_user)
        response = self.client.post(
            f"/api/v1/players/{self.player.slug}/achievements/",
            {
                "title": "Melhor Marcador",
                "achievement_type": "top_scorer",
                "level": "national",
                "certificate": self._pdf("certificate.pdf"),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertTrue(payload["data"]["certificate_url"])
        self.assertEqual(PlayerAchievement.objects.filter(player=self.player).count(), 1)

    def test_player_can_still_add_achievement_with_external_urls(self):
        self.client.force_authenticate(user=self.player_user)
        response = self.client.post(
            f"/api/v1/players/{self.player.slug}/achievements/",
            {
                "title": "MVP da Liga",
                "achievement_type": "mvp",
                "level": "club",
                "trophy_image_url": "https://example.com/trophy.jpg",
                "certificate_url": "https://example.com/cert.pdf",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["data"]["trophy_image"], "https://example.com/trophy.jpg")
        self.assertEqual(payload["data"]["certificate_url"], "https://example.com/cert.pdf")
