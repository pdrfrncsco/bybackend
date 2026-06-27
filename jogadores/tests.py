from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
from PIL import Image
from rest_framework.test import APIClient

from core.models import Tenant
from clubs.models import Club
from .models import Player, PlayerHistory


User = get_user_model()


class PlayerApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.tenant1 = Tenant.objects.create(name="Tenant 1", slug="tenant-1")
        self.tenant2 = Tenant.objects.create(name="Tenant 2", slug="tenant-2")
        self.user1 = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="testpass",
            tenant=self.tenant1,
            role="manager",
        )
        self.user2 = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="testpass",
            tenant=self.tenant2,
            role="manager",
        )

        self.club1 = Club.objects.create(tenant=self.tenant1, name="Clube 1")
        self.club2 = Club.objects.create(tenant=self.tenant2, name="Clube 2")

        self.player1 = Player.objects.create(
            tenant=self.tenant1,
            name="Jogador Um",
            position="Avançado",
            number=9,
            age=22,
            nationality="Angolana",
            club=self.club1,
            status="active",
            height=180,
            weight=75,
            foot="Direito",
        )
        Player.objects.create(
            tenant=self.tenant2,
            name="Jogador Dois",
            position="Defesa",
            number=4,
            age=28,
            nationality="Angolana",
            club=self.club2,
            status="active",
            height=185,
            weight=80,
            foot="Direito",
        )

    def test_list_players_is_paginated_and_tenant_scoped(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get("/api/players/")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("results", body)
        self.assertEqual(len(body["results"]), 1)
        self.assertEqual(body["results"][0]["id"], str(self.player1.id))
        self.assertEqual(body["results"][0]["clubName"], "Clube 1")

    def test_filter_and_search_players(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get("/api/players/", {"search": "Um", "club": str(self.club1.id)})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(len(body["results"]), 1)

        response = self.client.get("/api/players/", {"search": "NaoExiste"})
        body = response.json()
        self.assertEqual(len(body["results"]), 0)

    def test_create_player_with_camelcase_payload(self):
        self.client.force_authenticate(user=self.user1)
        payload = {
            "name": "Novo Jogador",
            "position": "Meio-campo",
            "club": str(self.club1.id),
            "age": 19,
            "dateOfBirth": "2006-01-01",
            "nationality": "Angolana",
            "number": 10,
            "status": "active",
            "height": 175,
            "weight": 70,
            "foot": "Direito",
            "joinedDate": "2025-01-01",
            "history": [
                {
                    "season": "2024/2025",
                    "club": str(self.club1.id),
                    "matches": 12,
                    "goals": 3,
                    "assists": 1,
                }
            ],
        }
        response = self.client.post("/api/players/", payload, format="json")
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["clubName"], "Clube 1")
        self.assertEqual(len(body["history"]), 1)

    def test_create_player_with_avatar_upload(self):
        self.client.force_authenticate(user=self.user1)
        image_bytes = BytesIO()
        Image.new("RGBA", (1, 1), (255, 0, 0, 255)).save(image_bytes, format="PNG")
        avatar = SimpleUploadedFile("avatar.png", image_bytes.getvalue(), content_type="image/png")
        payload = {
            "name": "Jogador Avatar",
            "position": "Defesa",
            "club": str(self.club1.id),
            "age": 20,
            "nationality": "Angolana",
            "number": 2,
            "status": "active",
            "height": 180,
            "weight": 75,
            "foot": "Direito",
            "avatar": avatar,
        }
        response = self.client.post("/api/players/", payload, format="multipart")
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertIn("avatarUrl", body)

    def test_create_player_accepts_medio_position_and_ambos_foot(self):
        self.client.force_authenticate(user=self.user1)
        payload = {
            "name": "Jogador Médio",
            "position": "Médio",
            "club": str(self.club1.id),
            "nationality": "Angolana",
            "foot": "Ambos",
        }
        response = self.client.post("/api/players/", payload, format="json")
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["position"], "Meio-campo")
        self.assertEqual(body["foot"], "Ambos")

    def test_validation_errors_match_frontend_rules(self):
        self.client.force_authenticate(user=self.user1)
        payload = {
            "name": "X",
            "position": "Defesa",
            "club": str(self.club1.id),
            "age": 10,
            "nationality": "Angolana",
            "number": 120,
            "status": "active",
            "height": 90,
            "weight": 10,
            "foot": "Direito",
        }
        response = self.client.post("/api/players/", payload, format="json")
        self.assertEqual(response.status_code, 400)

    def test_patch_player_accepts_stats_field_from_frontend(self):
        self.client.force_authenticate(user=self.user1)
        payload = {
            "nickname": "Novo",
            "stats": {"matches": 10, "goals": 2, "assists": 1, "minutes": 100, "yellowCards": 1, "redCards": 0},
        }
        response = self.client.patch(f"/api/players/{self.player1.id}/", payload, format="json")
        self.assertEqual(response.status_code, 200)

    def test_create_rejects_other_tenant_club(self):
        self.client.force_authenticate(user=self.user1)
        payload = {
            "name": "Jogador Inválido",
            "position": "Defesa",
            "club": str(self.club2.id),
            "age": 20,
            "nationality": "Angolana",
            "number": 3,
            "status": "active",
            "height": 180,
            "weight": 75,
            "foot": "Direito",
        }
        response = self.client.post("/api/players/", payload, format="json")
        self.assertEqual(response.status_code, 400)

    def test_update_player_foot_is_persisted_and_normalized(self):
        self.client.force_authenticate(user=self.user1)
        payload = {"foot": "Ambos"}
        response = self.client.patch(f"/api/players/{self.player1.id}/", payload, format="json")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["foot"], "Ambos")
        self.player1.refresh_from_db()
        self.assertEqual(self.player1.foot, "Ambidestro")

    def test_update_player_avatar_upload_returns_avatar_url(self):
        self.client.force_authenticate(user=self.user1)
        image_bytes = BytesIO()
        Image.new("RGBA", (1, 1), (0, 255, 0, 255)).save(image_bytes, format="PNG")
        avatar = SimpleUploadedFile("new_avatar.png", image_bytes.getvalue(), content_type="image/png")
        payload = {"avatar": avatar}
        response = self.client.patch(f"/api/players/{self.player1.id}/", payload, format="multipart")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("avatarUrl", body)

    def test_update_player_multiple_fields_flow(self):
        self.client.force_authenticate(user=self.user1)
        payload = {
            "name": "Jogador Atualizado",
            "number": 10,
            "age": 25,
            "height": 185,
            "weight": 80,
            "foot": "Esquerdo",
            "status": "injured",
        }
        response = self.client.patch(f"/api/players/{self.player1.id}/", payload, format="json")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["name"], "Jogador Atualizado")
        self.assertEqual(body["number"], 10)
        self.assertEqual(body["age"], 25)
        self.assertEqual(body["height"], 185)
        self.assertEqual(body["weight"], 80)
        self.assertEqual(body["foot"], "Esquerdo")
        self.assertEqual(body["status"], "injured")

    def test_cannot_use_same_number_in_same_club(self):
        self.client.force_authenticate(user=self.user1)
        payload = {
            "name": "Jogador Duplicado",
            "position": "Defesa",
            "club": str(self.club1.id),
            "age": 23,
            "nationality": "Angolana",
            "number": self.player1.number,
            "status": "active",
            "height": 182,
            "weight": 76,
            "foot": "Direito",
        }
        response = self.client.post("/api/players/", payload, format="json")
        self.assertEqual(response.status_code, 400)
