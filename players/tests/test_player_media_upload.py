from datetime import date

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from players.models import Player, PlayerDocument, PlayerVideo

User = get_user_model()


class PlayerMediaUploadAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.staff_user = User.objects.create_user(
            email="staff@test.com",
            password="SecurePass123!",
            is_staff=True,
        )
        self.player_user = User.objects.create_user(
            email="player@test.com",
            password="SecurePass123!",
        )
        self.other_user = User.objects.create_user(
            email="other@test.com",
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

    def _pdf(self, name="contract.pdf"):
        return SimpleUploadedFile(name, b"%PDF-1.4 fake", content_type="application/pdf")

    def _mp4(self, name="highlights.mp4"):
        return SimpleUploadedFile(name, b"fake-video-content", content_type="video/mp4")

    def test_player_uploads_document_via_dam(self):
        self.client.force_authenticate(user=self.player_user)
        response = self.client.post(
            f"/api/v1/players/{self.player.slug}/documents/",
            {
                "title": "Contrato 2026",
                "category": "contract",
                "description": "Contrato principal",
                "document": self._pdf(),
                "is_private": False,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertTrue(payload["data"]["asset_url"])
        self.assertEqual(PlayerDocument.objects.filter(player=self.player).count(), 1)

    def test_linked_player_sees_own_pending_documents(self):
        from media_assets.models import MediaAsset

        asset = MediaAsset.objects.create(
            name="medical.pdf",
            original_filename="medical.pdf",
            object_key="test/medical.pdf",
            asset_type="document",
            category="document",
            mime_type="application/pdf",
            extension="pdf",
            size_bytes=1024,
        )
        PlayerDocument.objects.create(
            player=self.player,
            title="Privado",
            category=PlayerDocument.DocumentCategory.MEDICAL,
            asset=asset,
            is_private=True,
        )

        self.client.force_authenticate(user=self.player_user)
        response = self.client.get(f"/api/v1/players/{self.player.slug}/documents/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["data"]["results"]
        self.assertEqual(len(results), 1)

    def test_other_user_cannot_upload_document(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.post(
            f"/api/v1/players/{self.player.slug}/documents/",
            {
                "title": "Contrato",
                "category": "contract",
                "document": self._pdf(),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_player_uploads_video_file_via_dam(self):
        self.client.force_authenticate(user=self.player_user)
        response = self.client.post(
            f"/api/v1/players/{self.player.slug}/videos/",
            {
                "title": "Melhores momentos",
                "video_type": "highlights",
                "video": self._mp4(),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["data"]["status"], "draft")
        self.assertTrue(payload["data"]["media_asset"])
        self.assertEqual(PlayerVideo.objects.filter(player=self.player).count(), 1)

    def test_player_can_still_add_external_video_url(self):
        self.client.force_authenticate(user=self.player_user)
        response = self.client.post(
            f"/api/v1/players/{self.player.slug}/videos/",
            {
                "title": "Entrevista",
                "video_type": "interview",
                "video_url": "https://www.youtube.com/watch?v=example",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["data"]["video_url"], "https://www.youtube.com/watch?v=example")
