"""
Tests for PlayerCategory and Gender features.
"""

from datetime import date
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import Tenant
from clubs.models import Club
from players.models import Player, PlayerRegistration, PlayerCategory
from players.selectors import PlayerSelector


class PlayerCategoryTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Federação Angolana de Futebol", slug="faf")
        self.club = Club.objects.create(
            tenant=self.tenant,
            name="Petro Atlético de Luanda",
            slug="petro-luanda",
            gender="mixed",
        )
        self.category_senior = PlayerCategory.objects.create(
            tenant=self.tenant,
            name="Sénior",
            slug="senior",
            min_age=16,
            max_age=None,
            gender="mixed",
            display_order=8,
        )
        self.category_junior = PlayerCategory.objects.create(
            tenant=self.tenant,
            name="Júnior",
            slug="junior",
            min_age=18,
            max_age=23,
            gender="male",
            display_order=7,
        )
        self.category_iniciado = PlayerCategory.objects.create(
            tenant=self.tenant,
            name="Iniciado",
            slug="iniciado",
            min_age=14,
            max_age=16,
            gender="mixed",
            display_order=5,
        )

        today = date.today()
        # 20 years old
        self.player_male = Player.objects.create(
            first_name="Gilberto",
            last_name="Sebastião",
            gender="male",
            date_of_birth=date(today.year - 20, today.month, today.day),
        )
        # 15 years old
        self.player_youth = Player.objects.create(
            first_name="Zito",
            last_name="Luvumbo",
            gender="male",
            date_of_birth=date(today.year - 15, today.month, today.day),
        )

    def test_eligible_category_calculation(self):
        categories = [self.category_senior, self.category_junior, self.category_iniciado]
        # 20yo should match Junior first
        cat_20 = self.player_male.get_eligible_category(categories)
        self.assertEqual(cat_20.slug, "junior")

        # 15yo should match Iniciado
        cat_15 = self.player_youth.get_eligible_category(categories)
        self.assertEqual(cat_15.slug, "iniciado")

    def test_club_custom_category_creation(self):
        custom_cat = PlayerCategory.objects.create(
            tenant=self.tenant,
            club=self.club,
            name="Sub-17 B",
            slug="sub-17-b",
            min_age=15,
            max_age=17,
            gender="male",
        )
        self.assertTrue(custom_cat.is_custom)
        self.assertEqual(custom_cat.scope, PlayerCategory.Scope.CLUB)

    def test_squad_category_filtering(self):
        # Register players
        reg1 = PlayerRegistration.objects.create(
            player=self.player_male,
            club=self.club,
            tenant=self.tenant,
            category=self.category_junior,
            joined_date=date.today(),
            status="registered",
            shirt_number=10,
        )
        reg2 = PlayerRegistration.objects.create(
            player=self.player_youth,
            club=self.club,
            tenant=self.tenant,
            category=self.category_iniciado,
            joined_date=date.today(),
            status="registered",
            shirt_number=11,
        )

        client = APIClient()
        # Get squad filtered by junior
        res = client.get(f"/api/v1/clubs/public/{self.club.slug}/squad/?category_id={self.category_junior.id}")
        self.assertEqual(res.status_code, 200)
        data = res.json()["data"]
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["player_id"], str(self.player_male.id))
        self.assertEqual(data[0]["category_slug"], "junior")

    def test_club_categories_api(self):
        client = APIClient()
        res = client.get(f"/api/v1/clubs/{self.club.slug}/categories/")
        self.assertEqual(res.status_code, 200)
        cats = res.json()["data"]
        # Should contain the 3 federation categories
        self.assertGreaterEqual(len(cats), 3)
