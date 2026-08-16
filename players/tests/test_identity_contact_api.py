from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date

from media_assets.models import MediaAsset
from players.models import Player, PlayerContact, PlayerIdentityDocument
from players.services import PlayerService

User = get_user_model()


class PlayerIdentityContactAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Create a player
        self.player = Player.objects.create(
            first_name="Api",
            last_name="Player",
            slug="api-player",
            date_of_birth=date(2000, 1, 1),
            nationality="AO",
            primary_position="st",
            status="active",
        )
        # Create staff user
        self.staff = User.objects.create_superuser(username="staff", email="staff@test.com", password="pass1234")

    def test_get_contact_initially_none(self):
        resp = self.client.get(f"/api/v1/players/{self.player.slug}/contact/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['data'], {})

    def test_patch_contact_as_staff(self):
        self.client.force_authenticate(user=self.staff)
        payload = {
            "primary_email": "contact@example.com",
            "mobile_phone": "+244912345678",
            "country": "AO",
        }
        resp = self.client.patch(f"/api/v1/players/{self.player.slug}/contact/", data=payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.data['data']
        self.assertEqual(data['primary_email'], payload['primary_email'])
        self.assertEqual(data['mobile_phone'], payload['mobile_phone'])

        # Ensure persisted in DB
        contact = PlayerContact.objects.get(player=self.player)
        self.assertEqual(contact.primary_email, payload['primary_email'])

    def test_get_contact_public(self):
        # Create a contact via service to ensure data exists
        PlayerService.create_player(
            first_name="Temp",
            last_name="ForContact",
            date_of_birth=date(1999,1,1),
            nationality="AO",
            primary_position="cm",
            email=None,
            phone=None,
            height_cm=None,
            weight_kg=None,
            foot=None,
            bio=None,
            avatar=None,
        )
        # Upsert contact directly
        PlayerContact.objects.create(player=self.player, primary_email="public@example.com", mobile_phone="+244900000000", country="AO")
        resp = self.client.get(f"/api/v1/players/{self.player.slug}/contact/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(resp.data['data'])
        self.assertEqual(resp.data['data']['primary_email'], "public@example.com")

    def test_get_contact_for_linked_player_before_public(self):
        linked_user = User.objects.create_user(username="linked", email="linked@test.com", password="pass1234")
        self.player.user = linked_user
        self.player.is_public = False
        self.player.save(update_fields=["user", "is_public"])

        self.client.force_authenticate(user=linked_user)

        resp = self.client.get(f"/api/v1/players/{self.player.slug}/contact/")

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["data"], {})

    def test_create_identity_document_persists_front_back_and_blank_number(self):
        linked_user = User.objects.create_user(username="identity", email="identity@test.com", password="pass1234")
        self.player.user = linked_user
        self.player.save(update_fields=["user"])

        front_asset = MediaAsset.objects.create(
            name="identity-front.pdf",
            original_filename="identity-front.pdf",
            object_key="test/identity-front.pdf",
            asset_type="document",
            category="document",
            mime_type="application/pdf",
            extension="pdf",
            size_bytes=1024,
        )
        back_asset = MediaAsset.objects.create(
            name="identity-back.pdf",
            original_filename="identity-back.pdf",
            object_key="test/identity-back.pdf",
            asset_type="document",
            category="document",
            mime_type="application/pdf",
            extension="pdf",
            size_bytes=1024,
        )

        with patch(
            "media_assets.services.MediaAssetService.upload_for_owner",
            side_effect=[front_asset, back_asset],
        ) as mocked_upload:
            self.client.force_authenticate(user=linked_user)
            response = self.client.post(
                f"/api/v1/players/{self.player.slug}/identity-documents/",
                {
                    "document_type": "national_id",
                    "document_front": SimpleUploadedFile("front.pdf", b"%PDF-1.4 front", content_type="application/pdf"),
                    "document_back": SimpleUploadedFile("back.pdf", b"%PDF-1.4 back", content_type="application/pdf"),
                },
                format="multipart",
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(mocked_upload.call_count, 2)
        document = PlayerIdentityDocument.objects.get(player=self.player)
        self.assertEqual(document.document_front_id, front_asset.id)
        self.assertEqual(document.document_back_id, back_asset.id)
        self.assertEqual(document.document_number, "")
