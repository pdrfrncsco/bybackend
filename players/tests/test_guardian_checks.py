from django.test import TestCase
from datetime import date, timedelta
from rest_framework.test import APIClient

from players.models import Player, LegalGuardian
from clubs.models import Club
from core.models import Tenant
from players.services import PlayerRegistrationService, GuardianConsentRequired


class GuardianChecksTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.tenant = Tenant.objects.create(name="GTest", slug="gtest")
        self.club = Club.objects.create(name="GClub", slug="gclub", tenant=self.tenant)

        # Create a minor player (16 years old)
        sixteen_years_ago = date.today() - timedelta(days=16 * 365)
        self.player_minor = Player.objects.create(
            first_name="Minor",
            last_name="Player",
            slug="minor-player",
            date_of_birth=sixteen_years_ago,
            nationality="AO",
            primary_position="st",
            status="active",
        )

    def test_register_minor_without_guardian_raises(self):
        with self.assertRaises(GuardianConsentRequired):
            PlayerRegistrationService.register_player(
                player=self.player_minor,
                club=self.club,
                tenant=self.tenant,
                joined_date=date.today(),
            )

    def test_register_minor_with_guardian_succeeds(self):
        # Add guardian with consent
        LegalGuardian.objects.create(
            player=self.player_minor,
            name="Parent",
            relationship="father",
            phone="+244900000000",
            consent_status="given",
        )

        reg = PlayerRegistrationService.register_player(
            player=self.player_minor,
            club=self.club,
            tenant=self.tenant,
            joined_date=date.today(),
        )
        self.assertIsNotNone(reg)
        self.assertEqual(reg.player.id, self.player_minor.id)
