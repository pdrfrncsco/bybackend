"""
BOLAYETU — Fair Play & Ranking Tests

Tests for PlayerSuspension, FairPlayService, and RankingService.
"""

from django.test import TestCase
from django.utils import timezone
from datetime import date, timedelta
from django.contrib.auth import get_user_model

from core.models import Tenant
from players.models import Player
from clubs.models import Club
from competitions.models import (
    Competition,
    Match,
    MatchEvent,
    PlayerSuspension,
    CompetitionRanking,
)
from competitions.services.fair_play_service import (
    FairPlayService,
    FairPlayConfig,
    SuspensionAlreadyExists,
)
from competitions.services.ranking_service import RankingService


User = get_user_model()


class FairPlayServiceTestCase(TestCase):
    """Test FairPlayService functionality."""

    def setUp(self):
        """Set up test data."""
        self.tenant = Tenant.objects.create(
            name="Test Federation",
            slug="test-fed",
            type="federation",
        )
        self.player = Player.objects.create(
            first_name="João",
            last_name="Silva",
            slug="joao-silva",
            nationality="AO",
            primary_position="ST",
        )
        self.club = Club.objects.create(
            name="Petro de Luanda",
            slug="petro-luanda",
            tenant=self.tenant,
        )
        self.competition = Competition.objects.create(
            name="Girabola 2025",
            tenant=self.tenant,
            season="2024/2025",
        )
        self.away_club = Club.objects.create(
            name="1º de Agosto",
            slug="1-agosto",
            tenant=self.tenant,
        )
        self.match = Match.objects.create(
            competition=self.competition,
            tenant=self.tenant,
            home_club=self.club,
            away_club=self.away_club,
            match_date=timezone.now(),
            round_number=1,
        )

    def test_get_player_cards_for_competition(self):
        """Test counting cards for a player in a competition."""
        # Create some card events
        MatchEvent.objects.create(
            tenant=self.tenant,
            match=self.match,
            club=self.club,
            player=self.player,
            event_type=MatchEvent.EventType.YELLOW_CARD,
            minute=30,
        )
        MatchEvent.objects.create(
            tenant=self.tenant,
            match=self.match,
            club=self.club,
            player=self.player,
            event_type=MatchEvent.EventType.YELLOW_CARD,
            minute=60,
        )
        MatchEvent.objects.create(
            tenant=self.tenant,
            match=self.match,
            club=self.club,
            player=self.player,
            event_type=MatchEvent.EventType.RED_CARD,
            minute=85,
        )

        cards = FairPlayService.get_player_cards_for_competition(
            tenant=self.tenant,
            player=self.player,
            competition=self.competition,
        )

        self.assertEqual(cards["yellow_cards"], 2)
        self.assertEqual(cards["red_cards"], 1)
        self.assertEqual(cards["yellow_reds"], 0)
        self.assertEqual(cards["total_cards"], 3)

    def test_create_suspension_for_red_card(self):
        """Test automatic suspension for direct red card."""
        red_event = MatchEvent.objects.create(
            tenant=self.tenant,
            match=self.match,
            club=self.club,
            player=self.player,
            event_type=MatchEvent.EventType.RED_CARD,
            minute=75,
        )

        suspension = FairPlayService.check_and_create_suspension_for_event(
            tenant=self.tenant,
            event=red_event,
        )

        self.assertIsNotNone(suspension)
        self.assertEqual(suspension.suspension_type, PlayerSuspension.SuspensionType.RED_CARD)
        self.assertEqual(suspension.matches_suspended, 1)
        self.assertEqual(suspension.status, PlayerSuspension.SuspensionStatus.ACTIVE)
        self.assertEqual(suspension.player, self.player)
        self.assertEqual(suspension.competition, self.competition)

    def test_create_suspension_for_yellow_red(self):
        """Test automatic suspension for yellow-red (second yellow)."""
        yellow_red_event = MatchEvent.objects.create(
            tenant=self.tenant,
            match=self.match,
            club=self.club,
            player=self.player,
            event_type=MatchEvent.EventType.YELLOW_RED,
            minute=80,
        )

        suspension = FairPlayService.check_and_create_suspension_for_event(
            tenant=self.tenant,
            event=yellow_red_event,
        )

        self.assertIsNotNone(suspension)
        self.assertEqual(suspension.suspension_type, PlayerSuspension.SuspensionType.YELLOW_RED)
        self.assertEqual(suspension.matches_suspended, 1)

    def test_create_suspension_for_yellow_accumulation(self):
        """Test automatic suspension after accumulating yellow cards."""
        # Create 4 yellow cards first
        for minute in [10, 25, 45, 60]:
            event = MatchEvent.objects.create(
                tenant=self.tenant,
                match=self.match,
                club=self.club,
                player=self.player,
                event_type=MatchEvent.EventType.YELLOW_CARD,
                minute=minute,
            )
            FairPlayService.check_and_create_suspension_for_event(
                tenant=self.tenant,
                event=event,
            )

        # No suspension yet
        self.assertEqual(
            PlayerSuspension.objects.filter(
                player=self.player,
                competition=self.competition,
            ).count(),
            0
        )

        # 5th yellow card triggers suspension
        fifth_yellow = MatchEvent.objects.create(
            tenant=self.tenant,
            match=self.match,
            club=self.club,
            player=self.player,
            event_type=MatchEvent.EventType.YELLOW_CARD,
            minute=75,
        )

        suspension = FairPlayService.check_and_create_suspension_for_event(
            tenant=self.tenant,
            event=fifth_yellow,
        )

        self.assertIsNotNone(suspension)
        self.assertEqual(
            suspension.suspension_type,
            PlayerSuspension.SuspensionType.YELLOW_ACCUMULATION
        )
        self.assertEqual(suspension.matches_suspended, 1)

    def test_is_player_eligible(self):
        """Test player eligibility check."""
        # Player should be eligible initially
        is_eligible, reason = FairPlayService.is_player_eligible(
            tenant=self.tenant,
            player=self.player,
            competition=self.competition,
        )
        self.assertTrue(is_eligible)
        self.assertIsNone(reason)

        # Create suspension
        suspension = FairPlayService.create_suspension(
            tenant=self.tenant,
            player=self.player,
            club=self.club,
            competition=self.competition,
            suspension_type=PlayerSuspension.SuspensionType.RED_CARD,
            matches_suspended=1,
            effective_from=date.today(),
        )

        # Player should not be eligible
        is_eligible, reason = FairPlayService.is_player_eligible(
            tenant=self.tenant,
            player=self.player,
            competition=self.competition,
        )
        self.assertFalse(is_eligible)
        self.assertIn("suspenso", reason.lower())

    def test_serve_match(self):
        """Test that suspension is served after matches."""
        suspension = FairPlayService.create_suspension(
            tenant=self.tenant,
            player=self.player,
            club=self.club,
            competition=self.competition,
            suspension_type=PlayerSuspension.SuspensionType.RED_CARD,
            matches_suspended=1,
            effective_from=date.today(),
        )

        self.assertEqual(suspension.matches_served, 0)
        self.assertEqual(suspension.remaining_matches, 1)
        self.assertEqual(suspension.status, PlayerSuspension.SuspensionStatus.ACTIVE)

        # Simulate match served
        suspension.serve_match()

        suspension.refresh_from_db()
        self.assertEqual(suspension.matches_served, 1)
        self.assertEqual(suspension.remaining_matches, 0)
        self.assertEqual(suspension.status, PlayerSuspension.SuspensionStatus.SERVED)
        self.assertIsNotNone(suspension.served_on)

    def test_cancel_suspension(self):
        """Test cancelling a suspension."""
        user = User.objects.create_user(
            email="admin@test.com",
            password="testpass123",
        )

        suspension = FairPlayService.create_suspension(
            tenant=self.tenant,
            player=self.player,
            club=self.club,
            competition=self.competition,
            suspension_type=PlayerSuspension.SuspensionType.RED_CARD,
            matches_suspended=1,
            effective_from=date.today(),
        )

        self.assertEqual(suspension.status, PlayerSuspension.SuspensionStatus.ACTIVE)

        suspension.cancel(user=user, reason="Appeal accepted")

        suspension.refresh_from_db()
        self.assertEqual(suspension.status, PlayerSuspension.SuspensionStatus.CANCELLED)
        self.assertEqual(suspension.cancelled_by, user)
        self.assertEqual(suspension.cancellation_reason, "Appeal accepted")
        self.assertIsNotNone(suspension.cancelled_at)

    def test_duplicate_suspension_prevention(self):
        """Test that duplicate active suspensions are prevented."""
        FairPlayService.create_suspension(
            tenant=self.tenant,
            player=self.player,
            club=self.club,
            competition=self.competition,
            suspension_type=PlayerSuspension.SuspensionType.RED_CARD,
            matches_suspended=1,
            effective_from=date.today(),
        )

        with self.assertRaises(SuspensionAlreadyExists):
            FairPlayService.create_suspension(
                tenant=self.tenant,
                player=self.player,
                club=self.club,
                competition=self.competition,
                suspension_type=PlayerSuspension.SuspensionType.YELLOW_ACCUMULATION,
                matches_suspended=1,
                effective_from=date.today(),
            )


class RankingServiceTestCase(TestCase):
    """Test RankingService functionality."""

    def setUp(self):
        """Set up test data."""
        self.tenant = Tenant.objects.create(
            name="Test Federation",
            slug="test-fed",
            type="federation",
        )
        self.player1 = Player.objects.create(
            first_name="João",
            last_name="Silva",
            slug="joao-silva",
            nationality="AO",
            primary_position="ST",
        )
        self.player2 = Player.objects.create(
            first_name="Pedro",
            last_name="Santos",
            slug="pedro-santos",
            nationality="AO",
            primary_position="CF",
        )
        self.club = Club.objects.create(
            name="Petro de Luanda",
            slug="petro-luanda",
            tenant=self.tenant,
        )
        self.away_club = Club.objects.create(
            name="1º de Agosto",
            slug="1-agosto",
            tenant=self.tenant,
        )
        self.competition = Competition.objects.create(
            name="Girabola 2025",
            tenant=self.tenant,
            season="2024/2025",
        )
        self.match = Match.objects.create(
            competition=self.competition,
            tenant=self.tenant,
            home_club=self.club,
            away_club=self.away_club,
            match_date=timezone.now(),
            round_number=1,
            status=Match.MatchStatus.FINISHED,
            home_score=3,
            away_score=1,
        )

    def test_calculate_top_scorers(self):
        """Test top scorers ranking calculation."""
        # Player 1: 3 goals
        for minute in [10, 45, 70]:
            MatchEvent.objects.create(
                tenant=self.tenant,
                match=self.match,
                club=self.club,
                player=self.player1,
                event_type=MatchEvent.EventType.GOAL,
                minute=minute,
            )

        # Player 2: 1 goal
        MatchEvent.objects.create(
            tenant=self.tenant,
            match=self.match,
            club=self.club,
            player=self.player2,
            event_type=MatchEvent.EventType.GOAL,
            minute=30,
        )

        rankings = RankingService.calculate_top_scorers_for_season(
            tenant=self.tenant,
            season="2024/2025",
        )

        self.assertEqual(len(rankings), 2)
        
        # Check positions
        first = [r for r in rankings if r.player == self.player1][0]
        second = [r for r in rankings if r.player == self.player2][0]
        
        self.assertEqual(first.position, 1)
        self.assertEqual(first.value, 3)
        self.assertEqual(second.position, 2)
        self.assertEqual(second.value, 1)

    def test_get_top_scorers(self):
        """Test retrieving top scorers."""
        # Create some goal events
        for minute in [10, 45]:
            MatchEvent.objects.create(
                tenant=self.tenant,
                match=self.match,
                club=self.club,
                player=self.player1,
                event_type=MatchEvent.EventType.GOAL,
                minute=minute,
            )

        # Calculate rankings
        RankingService.calculate_top_scorers_for_season(
            tenant=self.tenant,
            season="2024/2025",
        )

        # Retrieve via service
        scorers = RankingService.get_top_scorers(
            tenant=self.tenant,
            season="2024/2025",
            limit=10,
        )

        self.assertEqual(len(scorers), 1)
        self.assertEqual(scorers[0]["player_name"], self.player1.full_name)
        self.assertEqual(scorers[0]["goals"], 2)

    def test_calculate_fair_play_ranking(self):
        """Test fair play ranking calculation."""
        # Club 1: 3 yellows, 1 red
        MatchEvent.objects.create(
            tenant=self.tenant,
            match=self.match,
            club=self.club,
            player=self.player1,
            event_type=MatchEvent.EventType.YELLOW_CARD,
            minute=10,
        )
        MatchEvent.objects.create(
            tenant=self.tenant,
            match=self.match,
            club=self.club,
            player=self.player1,
            event_type=MatchEvent.EventType.YELLOW_CARD,
            minute=30,
        )
        MatchEvent.objects.create(
            tenant=self.tenant,
            match=self.match,
            club=self.club,
            player=self.player1,
            event_type=MatchEvent.EventType.YELLOW_CARD,
            minute=50,
        )
        MatchEvent.objects.create(
            tenant=self.tenant,
            match=self.match,
            club=self.club,
            player=self.player1,
            event_type=MatchEvent.EventType.RED_CARD,
            minute=70,
        )

        # Club 2: 1 yellow
        MatchEvent.objects.create(
            tenant=self.tenant,
            match=self.match,
            club=self.away_club,
            player=self.player2,
            event_type=MatchEvent.EventType.YELLOW_CARD,
            minute=60,
        )

        rankings = RankingService.calculate_fair_play_ranking(
            tenant=self.tenant,
            season="2024/2025",
        )

        self.assertEqual(len(rankings), 2)
        
        # Lower score = better fair play
        club1_ranking = [r for r in rankings if r.club == self.club][0]
        club2_ranking = [r for r in rankings if r.club == self.away_club][0]
        
        # Club 1: 3*1 + 5 = 8
        # Club 2: 1*1 = 1
        self.assertEqual(club1_ranking.value, 8)
        self.assertEqual(club2_ranking.value, 1)
        
        # Club 2 should be in better position (lower score)
        self.assertLess(club2_ranking.position, club1_ranking.position)

    def test_fair_play_score_calculation(self):
        """Test that fair play scoring is correct."""
        from competitions.services.fair_play_service import FairPlayService
        
        fair_play = FairPlayService.get_fair_play_ranking_for_competition(
            tenant=self.tenant,
            competition=self.competition,
        )
        
        # No cards yet, all clubs should have score 0
        for entry in fair_play:
            self.assertEqual(entry["fair_play_score"], 0)


class CompetitionRankingModelTestCase(TestCase):
    """Test CompetitionRanking model."""

    def setUp(self):
        """Set up test data."""
        self.tenant = Tenant.objects.create(
            name="Test Federation",
            slug="test-fed",
            type="federation",
        )
        self.player = Player.objects.create(
            first_name="João",
            last_name="Silva",
            slug="joao-silva",
            nationality="AO",
            primary_position="ST",
        )
        self.club = Club.objects.create(
            name="Petro de Luanda",
            slug="petro-luanda",
            tenant=self.tenant,
        )

    def test_create_player_ranking(self):
        """Test creating a player ranking."""
        ranking = CompetitionRanking.objects.create(
            tenant=self.tenant,
            player=self.player,
            ranking_type=CompetitionRanking.RankingType.TOP_SCORER,
            aggregation_level=CompetitionRanking.AggregationLevel.SEASON,
            season="2024/2025",
            position=1,
            value=15,
            stats={"goals": 15, "matches": 20},
        )

        self.assertEqual(ranking.position, 1)
        self.assertEqual(ranking.value, 15)
        self.assertEqual(ranking.stats["goals"], 15)
        self.assertFalse(ranking.is_official)

    def test_create_club_ranking(self):
        """Test creating a club ranking."""
        ranking = CompetitionRanking.objects.create(
            tenant=self.tenant,
            club=self.club,
            ranking_type=CompetitionRanking.RankingType.FAIR_PLAY_CLUB,
            aggregation_level=CompetitionRanking.AggregationLevel.SEASON,
            season="2024/2025",
            position=5,
            value=12,
            stats={"yellow_cards": 10, "red_cards": 2},
        )

        self.assertEqual(ranking.position, 5)
        self.assertEqual(ranking.value, 12)
        self.assertEqual(ranking.stats["yellow_cards"], 10)

    def test_position_change(self):
        """Test position change tracking."""
        ranking = CompetitionRanking.objects.create(
            tenant=self.tenant,
            player=self.player,
            ranking_type=CompetitionRanking.RankingType.TOP_SCORER,
            aggregation_level=CompetitionRanking.AggregationLevel.SEASON,
            season="2024/2025",
            position=3,
            previous_position=5,
            value=10,
        )

        # Moved up from 5 to 3 = +2
        self.assertEqual(ranking.position_change, 2)
        self.assertTrue(ranking.moved_up)
        self.assertFalse(ranking.moved_down)

    def test_update_position(self):
        """Test updating position."""
        ranking = CompetitionRanking.objects.create(
            tenant=self.tenant,
            player=self.player,
            ranking_type=CompetitionRanking.RankingType.TOP_SCORER,
            aggregation_level=CompetitionRanking.AggregationLevel.SEASON,
            season="2024/2025",
            position=3,
            value=10,
        )

        ranking.update_position(1)

        self.assertEqual(ranking.position, 1)
        self.assertEqual(ranking.previous_position, 3)


class PlayerSuspensionModelTestCase(TestCase):
    """Test PlayerSuspension model."""

    def setUp(self):
        """Set up test data."""
        self.tenant = Tenant.objects.create(
            name="Test Federation",
            slug="test-fed",
            type="federation",
        )
        self.player = Player.objects.create(
            first_name="João",
            last_name="Silva",
            slug="joao-silva",
            nationality="AO",
            primary_position="ST",
        )
        self.club = Club.objects.create(
            name="Petro de Luanda",
            slug="petro-luanda",
            tenant=self.tenant,
        )
        self.competition = Competition.objects.create(
            name="Girabola 2025",
            tenant=self.tenant,
        )

    def test_create_suspension(self):
        """Test creating a suspension."""
        suspension = PlayerSuspension.objects.create(
            tenant=self.tenant,
            player=self.player,
            club=self.club,
            competition=self.competition,
            suspension_type=PlayerSuspension.SuspensionType.RED_CARD,
            matches_suspended=1,
            effective_from=date.today(),
        )

        self.assertEqual(suspension.status, PlayerSuspension.SuspensionStatus.PENDING)
        self.assertEqual(suspension.matches_suspended, 1)
        self.assertEqual(suspension.matches_served, 0)
        self.assertEqual(suspension.remaining_matches, 1)

    def test_suspension_properties(self):
        """Test suspension properties."""
        suspension = PlayerSuspension.objects.create(
            tenant=self.tenant,
            player=self.player,
            club=self.club,
            competition=self.competition,
            suspension_type=PlayerSuspension.SuspensionType.YELLOW_ACCUMULATION,
            matches_suspended=2,
            effective_from=date.today(),
        )

        self.assertTrue(suspension.is_pending)
        self.assertFalse(suspension.is_active)
        self.assertFalse(suspension.is_fully_served)

        # Activate
        suspension.activate()
        self.assertFalse(suspension.is_pending)
        self.assertTrue(suspension.is_active)

        # Serve one match
        suspension.serve_match()
        self.assertEqual(suspension.matches_served, 1)
        self.assertEqual(suspension.remaining_matches, 1)
        self.assertFalse(suspension.is_fully_served)

        # Serve second match
        suspension.serve_match()
        self.assertEqual(suspension.matches_served, 2)
        self.assertEqual(suspension.remaining_matches, 0)
        self.assertTrue(suspension.is_fully_served)
        self.assertEqual(suspension.status, PlayerSuspension.SuspensionStatus.SERVED)
