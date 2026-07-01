from django.test import TestCase
from datetime import datetime
from core.models import Tenant
from clubs.models import Club
from competitions.models import Competition, CompetitionRegistration, Match, Standing
from competitions.services import CompetitionService
from competitions.services.competition_registration_service import CompetitionRegistrationService, ClubAlreadyRegistered
from competitions.services.match_service import MatchService
from competitions.services.standing_service import StandingService


class CompetitionServicesTestCase(TestCase):
    def setUp(self):
        # Create tenant
        self.tenant = Tenant.objects.create(name="Test Federation", slug="test-fed")
        
        # Create competition
        self.competition = CompetitionService.create_competition(
            tenant=self.tenant,
            name="Girabola",
            competition_type="league",
            season="2025/26",
        )
        
        # Create clubs
        self.club1 = Club.objects.create(name="Petro de Luanda", slug="petro-luanda", tenant=self.tenant, city="Luanda")
        self.club2 = Club.objects.create(name="1º de Agosto", slug="primeiro-agosto", tenant=self.tenant, city="Luanda")
        self.club3 = Club.objects.create(name="Sagrada Esperança", slug="sagrada-esperanca", tenant=self.tenant, city="Dundo")
        self.club4 = Club.objects.create(name="Wiliete de Benguela", slug="wiliete-benguela", tenant=self.tenant, city="Benguela")

    def test_register_club_creates_standing(self):
        """Test registering a club creates a registration and standing entry."""
        reg = CompetitionRegistrationService.register_club(
            tenant=self.tenant,
            competition=self.competition,
            club=self.club1,
        )
        self.assertIsNotNone(reg)
        self.assertEqual(reg.club, self.club1)
        self.assertEqual(reg.competition, self.competition)
        
        # Verify standing is initialized
        standing = Standing.objects.get(competition=self.competition, club=self.club1)
        self.assertEqual(standing.points, 0)
        self.assertEqual(standing.played, 0)
        self.assertEqual(standing.position, 1)

    def test_duplicate_registration_fails(self):
        """Test that registering the same club twice raises ClubAlreadyRegistered."""
        CompetitionRegistrationService.register_club(
            tenant=self.tenant,
            competition=self.competition,
            club=self.club1,
        )
        
        with self.assertRaises(ClubAlreadyRegistered):
            CompetitionRegistrationService.register_club(
                tenant=self.tenant,
                competition=self.competition,
                club=self.club1,
            )

    def test_generate_berger_schedule_even_teams(self):
        """Test round-robin generator for even number of clubs."""
        # Register 4 clubs (even)
        for club in [self.club1, self.club2, self.club3, self.club4]:
            CompetitionRegistrationService.register_club(
                tenant=self.tenant,
                competition=self.competition,
                club=club,
            )

        start_date = datetime(2026, 8, 1, 16, 0)
        # Double round-robin: 4 teams = 6 rounds of 2 matches = 12 matches total
        matches = MatchService.generate_round_robin_schedule(
            tenant=self.tenant,
            competition=self.competition,
            start_date=start_date,
            double_round=True,
        )

        self.assertEqual(len(matches), 12)
        # Verify 6 rounds
        rounds = set(m.round_number for m in matches)
        self.assertEqual(rounds, {1, 2, 3, 4, 5, 6})

    def test_generate_berger_schedule_odd_teams(self):
        """Test round-robin generator for odd number of clubs."""
        # Register 3 clubs (odd)
        for club in [self.club1, self.club2, self.club3]:
            CompetitionRegistrationService.register_club(
                tenant=self.tenant,
                competition=self.competition,
                club=club,
            )

        start_date = datetime(2026, 8, 1, 16, 0)
        # 3 teams -> treated as 4 with bye.
        # N rounds = 3. Double round-robin = 6 rounds.
        # Each round has 1 match (the other team has bye).
        # Total matches = 6 rounds * 1 match = 6 matches.
        matches = MatchService.generate_round_robin_schedule(
            tenant=self.tenant,
            competition=self.competition,
            start_date=start_date,
            double_round=True,
        )

        self.assertEqual(len(matches), 6)

    def test_match_score_update_recalculates_standings(self):
        """Test that updating a match score updates standings and points correctly."""
        # Register 2 clubs
        for club in [self.club1, self.club2]:
            CompetitionRegistrationService.register_club(
                tenant=self.tenant,
                competition=self.competition,
                club=club,
            )

        # Create a match
        match = Match.objects.create(
            competition=self.competition,
            tenant=self.tenant,
            home_club=self.club1,
            away_club=self.club2,
            match_date=datetime(2026, 8, 1, 16, 0),
            round_number=1,
            status=Match.MatchStatus.SCHEDULED,
        )

        # Petro de Luanda (club1) wins 2 - 1 against 1º de Agosto (club2)
        MatchService.update_match_score(
            tenant=self.tenant,
            match_id=match.id,
            home_score=2,
            away_score=1,
        )

        # Verify standings
        standing1 = Standing.objects.get(competition=self.competition, club=self.club1)
        standing2 = Standing.objects.get(competition=self.competition, club=self.club2)

        self.assertEqual(standing1.points, 3)
        self.assertEqual(standing1.played, 1)
        self.assertEqual(standing1.won, 1)
        self.assertEqual(standing1.goals_for, 2)
        self.assertEqual(standing1.goals_against, 1)
        self.assertEqual(standing1.goal_difference, 1)
        self.assertEqual(standing1.position, 1)

        self.assertEqual(standing2.points, 0)
        self.assertEqual(standing2.played, 1)
        self.assertEqual(standing2.lost, 1)
        self.assertEqual(standing2.goals_for, 1)
        self.assertEqual(standing2.goals_against, 2)
        self.assertEqual(standing2.goal_difference, -1)
        self.assertEqual(standing2.position, 2)
