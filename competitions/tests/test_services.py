from django.test import TestCase
from datetime import datetime, timezone
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

        start_date = datetime(2026, 8, 1, 16, 0, tzinfo=timezone.utc)
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

        start_date = datetime(2026, 8, 1, 16, 0, tzinfo=timezone.utc)
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

    def test_create_competition_persists_config(self):
        """Competition creation should store config payloads."""
        competition = CompetitionService.create_competition(
            tenant=self.tenant,
            name="Taça Teste",
            competition_type="cup",
            season="2025/26",
            config={"pointsWin": 5, "settings": {"doubleRound": False}},
        )

        self.assertEqual(competition.config["pointsWin"], 5)
        self.assertFalse(competition.config["settings"]["doubleRound"])

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
            match_date=datetime(2026, 8, 1, 16, 0, tzinfo=timezone.utc),
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

    def test_match_score_update_uses_configured_points(self):
        """Points should follow competition config, not hardcoded 3/1/0."""
        competition = CompetitionService.create_competition(
            tenant=self.tenant,
            name="Cup Config",
            competition_type="cup",
            season="2025/26",
            config={"pointsWin": 5, "pointsDraw": 2, "pointsLoss": 0},
        )

        for club in [self.club1, self.club2]:
            CompetitionRegistrationService.register_club(
                tenant=self.tenant,
                competition=competition,
                club=club,
            )

        match = Match.objects.create(
            competition=competition,
            tenant=self.tenant,
            home_club=self.club1,
            away_club=self.club2,
            match_date=datetime(2026, 8, 1, 16, 0, tzinfo=timezone.utc),
            round_number=1,
            status=Match.MatchStatus.SCHEDULED,
        )

        MatchService.update_match_score(
            tenant=self.tenant,
            match_id=match.id,
            home_score=1,
            away_score=0,
        )

        standing1 = Standing.objects.get(competition=competition, club=self.club1)
        standing2 = Standing.objects.get(competition=competition, club=self.club2)

        self.assertEqual(standing1.points, 5)
        self.assertEqual(standing2.points, 0)

    def test_head_to_head_tiebreaker_overrides_goal_difference(self):
        """Head-to-head should rank teams before goal difference when configured."""
        competition = CompetitionService.create_competition(
            tenant=self.tenant,
            name="Tiebreak Cup",
            competition_type="cup",
            season="2025/26",
            config={
                "pointsWin": 3,
                "pointsDraw": 1,
                "pointsLoss": 0,
                "tiebreakers": ["points", "headToHead", "goalDifference", "goalsFor"],
            },
        )

        clubs = [self.club1, self.club2, self.club3, self.club4]
        for club in clubs:
            CompetitionRegistrationService.register_club(
                tenant=self.tenant,
                competition=competition,
                club=club,
            )

        # A beats B, but B has better goal difference from other results.
        fixtures = [
            (self.club1, self.club2, 1, 0),
            (self.club1, self.club3, 1, 0),
            (self.club1, self.club4, 0, 1),
            (self.club2, self.club3, 3, 0),
            (self.club2, self.club4, 3, 0),
        ]
        for home, away, home_score, away_score in fixtures:
            Match.objects.create(
                competition=competition,
                tenant=self.tenant,
                home_club=home,
                away_club=away,
                match_date=datetime(2026, 8, 1, 16, 0, tzinfo=timezone.utc),
                round_number=1,
                status=Match.MatchStatus.FINISHED,
                home_score=home_score,
                away_score=away_score,
            )

        standings = StandingService.recalculate_standings(
            tenant=self.tenant,
            competition=competition,
        )

        standing1 = next(item for item in standings if item.club_id == self.club1.id)
        standing2 = next(item for item in standings if item.club_id == self.club2.id)

        self.assertEqual(standing1.points, 6)
        self.assertEqual(standing2.points, 6)
        self.assertGreater(standing2.goal_difference, standing1.goal_difference)
        self.assertEqual(standing1.position, 1)
        self.assertEqual(standing2.position, 2)

    def test_knockout_progression_creates_next_round_after_semis(self):
        """Completing knockout matches should auto-create the next round."""
        competition = CompetitionService.create_competition(
            tenant=self.tenant,
            name="Cup Progression",
            competition_type="cup",
            season="2025/26",
        )

        clubs = [self.club1, self.club2, self.club3, self.club4]
        for club in clubs:
            CompetitionRegistrationService.register_club(
                tenant=self.tenant,
                competition=competition,
                club=club,
            )

        from competitions.services.competition_format_service import CompetitionFormatService

        CompetitionFormatService.generate_draw(
            tenant=self.tenant,
            competition=competition,
            start_date=datetime(2026, 8, 1, 16, 0, tzinfo=timezone.utc),
            seed="fixed-seed",
        )

        semi_matches = list(
            Match.objects.filter(
                competition=competition,
                tenant=self.tenant,
                phase="knockout",
                round_number=1,
            ).order_by("created_at")
        )
        self.assertEqual(len(semi_matches), 2)

        MatchService.update_match_score(
            tenant=self.tenant,
            match_id=semi_matches[0].id,
            home_score=2,
            away_score=0,
        )
        MatchService.update_match_score(
            tenant=self.tenant,
            match_id=semi_matches[1].id,
            home_score=1,
            away_score=0,
        )

        final_matches = Match.objects.filter(
            competition=competition,
            tenant=self.tenant,
            phase="knockout",
            round_number=2,
        )
        self.assertEqual(final_matches.count(), 1)
        final_match = final_matches.first()
        self.assertEqual(final_match.round_name, "Final")

    def test_create_and_update_competition_with_all_metadata_fields(self):
        """Competition creation and update should persist start_date, category, allowed_genders and other metadata."""
        from datetime import date
        from players.models import PlayerCategory

        category = PlayerCategory.objects.create(
            tenant=self.tenant,
            name="Sub-20",
            slug="sub-20",
            min_age=18,
            max_age=20,
            gender="male",
        )

        comp = CompetitionService.create_competition(
            tenant=self.tenant,
            name="Torneio Nacional Sub-20",
            competition_type="tournament",
            season="2025/26",
            category=category,
            allowed_genders="male",
            start_date=date(2026, 1, 10),
            end_date=date(2026, 6, 20),
            registration_start_date=date(2025, 11, 1),
            registration_end_date=date(2025, 12, 15),
            description="Competição oficial de escalão Sub-20",
        )

        self.assertEqual(comp.category, category)
        self.assertEqual(comp.allowed_genders, "male")
        self.assertEqual(comp.start_date, date(2026, 1, 10))
        self.assertEqual(comp.end_date, date(2026, 6, 20))
        self.assertEqual(comp.registration_start_date, date(2025, 11, 1))
        self.assertEqual(comp.registration_end_date, date(2025, 12, 15))
        self.assertEqual(comp.description, "Competição oficial de escalão Sub-20")

        # Test updating fields
        updated_comp = CompetitionService.update_competition(
            competition=comp,
            allowed_genders="female",
            start_date=date(2026, 2, 1),
            description="Descrição atualizada",
        )

        self.assertEqual(updated_comp.allowed_genders, "female")
        self.assertEqual(updated_comp.start_date, date(2026, 2, 1))
        self.assertEqual(updated_comp.description, "Descrição atualizada")

    def test_update_and_delete_match(self):
        """Test updating match metadata and deleting match."""
        CompetitionRegistrationService.register_club(tenant=self.tenant, competition=self.competition, club=self.club1)
        CompetitionRegistrationService.register_club(tenant=self.tenant, competition=self.competition, club=self.club2)

        match = MatchService.create_match(
            tenant=self.tenant,
            competition=self.competition,
            home_club=self.club1,
            away_club=self.club2,
            match_date=datetime(2026, 3, 15, 16, 0, tzinfo=timezone.utc),
            venue="Estádio 11 de Novembro",
            round_number=1,
        )
        self.assertEqual(match.venue, "Estádio 11 de Novembro")

        # Update match
        new_date = datetime(2026, 3, 16, 17, 0, tzinfo=timezone.utc)
        updated = MatchService.update_match(
            tenant=self.tenant,
            match_id=str(match.id),
            venue="Estádio dos Coqueiros",
            match_date=new_date,
            round_number=2,
            status=Match.MatchStatus.POSTPONED,
        )
        self.assertEqual(updated.venue, "Estádio dos Coqueiros")
        self.assertEqual(updated.round_number, 2)
        self.assertEqual(updated.status, Match.MatchStatus.POSTPONED)

        # Delete match
        match_id = str(updated.id)
        MatchService.delete_match(tenant=self.tenant, match_id=match_id)
        self.assertFalse(Match.objects.filter(id=match_id).exists())

    def test_delete_competition(self):
        """Test deleting a competition."""
        comp = CompetitionService.create_competition(
            tenant=self.tenant,
            name="Taça da Amizade",
            competition_type="cup",
            season="2025/26",
        )
        comp_id = str(comp.id)
        CompetitionService.delete_competition(tenant=self.tenant, competition_id=comp_id)
        self.assertFalse(Competition.objects.filter(id=comp_id).exists())

    def test_submit_manual_scoresheet(self):
        """Test submitting a full manual scoresheet with goals and cards."""
        from competitions.services.match_event_service import MatchEventService
        from competitions.models import MatchEvent
        from competitions.serializers.v2_serializers import StandingSerializer

        CompetitionRegistrationService.register_club(tenant=self.tenant, competition=self.competition, club=self.club1)
        CompetitionRegistrationService.register_club(tenant=self.tenant, competition=self.competition, club=self.club2)

        match = MatchService.create_match(
            tenant=self.tenant,
            competition=self.competition,
            home_club=self.club1,
            away_club=self.club2,
            match_date=datetime(2026, 4, 10, 15, 30, tzinfo=timezone.utc),
            round_number=1,
        )

        goals_data = [
            {"club_id": str(self.club1.id), "minute": 23, "event_type": "goal"},
            {"club_id": str(self.club1.id), "minute": 67, "event_type": "penalty_scored"},
            {"club_id": str(self.club2.id), "minute": 88, "event_type": "goal"},
        ]
        cards_data = [
            {"club_id": str(self.club2.id), "minute": 34, "event_type": "yellow_card"},
            {"club_id": str(self.club1.id), "minute": 75, "event_type": "yellow_card"},
        ]

        updated = MatchEventService.submit_manual_scoresheet(
            tenant=self.tenant,
            match=match,
            home_score=2,
            away_score=1,
            status=Match.MatchStatus.FINISHED,
            goals=goals_data,
            cards=cards_data,
        )

        self.assertEqual(updated.status, Match.MatchStatus.FINISHED)
        self.assertEqual(updated.home_score, 2)
        self.assertEqual(updated.away_score, 1)

        # Check events created
        events = MatchEvent.objects.filter(match=match)
        self.assertEqual(events.count(), 5)
        self.assertEqual(events.filter(event_type__in=["goal", "penalty_scored"]).count(), 3)
        self.assertEqual(events.filter(event_type="yellow_card").count(), 2)

        # Check standings and form
        st1 = Standing.objects.get(competition=self.competition, club=self.club1)
        st2 = Standing.objects.get(competition=self.competition, club=self.club2)
        self.assertEqual(st1.points, 3)
        self.assertEqual(st2.points, 0)

        serializer_data = StandingSerializer(st1).data
        self.assertEqual(serializer_data["form"], ["W"])


