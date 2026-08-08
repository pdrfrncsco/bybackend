from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date

from players.models import Player, PlayerContact
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
