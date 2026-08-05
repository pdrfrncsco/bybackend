"""
BOLAYETU — Lineup Integration Tests

Test lineup submission, validation, player eligibility, and lifecycle.
"""

import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import uuid

from core.models import Tenant
from players.models import Player
from clubs.models import Club
from competitions.models import (
    Competition, CompetitionRegistration, Match, MatchLineup, LineupSubmission, MatchReport, Goal
)
from competitions.services.lineup_service import (
    LineupService, LineupValidationError, PlayerNotEligible, LineupAlreadySubmitted
)
from competitions.services.match_report_service import MatchReportService
from competitions.services.fair_play_service import FairPlayService

User = get_user_model()


@pytest.mark.django_db
class TestLineupSubmission(TestCase):
    """Test lineup submission and validation."""

    def setUp(self):
        """Set up test data."""
        # Create tenant
        self.tenant = Tenant.objects.create(name="Test Org")

        # Create competition
        self.competition = Competition.objects.create(
            tenant=self.tenant,
            name="Test Competition",
            season="2024",
        )

        # Create clubs
        self.home_club = Club.objects.create(
            tenant=self.tenant,
            name="Home Team",
            slug="home-team",
        )

        self.away_club = Club.objects.create(
            tenant=self.tenant,
            name="Away Team",
            slug="away-team",
        )

        # Register clubs in competition
        CompetitionRegistration.objects.create(tenant=self.tenant, competition=self.competition, club=self.home_club)
        CompetitionRegistration.objects.create(tenant=self.tenant, competition=self.competition, club=self.away_club)

        # Create match
        self.match = Match.objects.create(
            tenant=self.tenant,
            competition=self.competition,
            home_club=self.home_club,
            away_club=self.away_club,
            match_date=timezone.now() + timedelta(days=1),
            status=Match.MatchStatus.SCHEDULED,
        )

        # Create players for home club
        self.gk = Player.objects.create(
            first_name="Goal",
            last_name="Keeper",
            primary_position=Player.Position.GK,
        )

        self.cb1 = Player.objects.create(
            first_name="Center",
            last_name="Back1",
            primary_position=Player.Position.CB,
        )

        self.cb2 = Player.objects.create(
            first_name="Center",
            last_name="Back2",
            primary_position=Player.Position.CB,
        )

        self.rb = Player.objects.create(
            first_name="Right",
            last_name="Back",
            primary_position=Player.Position.RB,
        )

        self.lb = Player.objects.create(
            first_name="Left",
            last_name="Back",
            primary_position=Player.Position.LB,
        )

        self.cm1 = Player.objects.create(
            first_name="Central",
            last_name="Mid1",
            primary_position=Player.Position.CM,
        )

        self.cm2 = Player.objects.create(
            first_name="Central",
            last_name="Mid2",
            primary_position=Player.Position.CM,
        )

        self.cdm = Player.objects.create(
            first_name="Defensive",
            last_name="Mid",
            primary_position=Player.Position.CDM,
        )

        self.rm = Player.objects.create(
            first_name="Right",
            last_name="Mid",
            primary_position=Player.Position.RM,
        )

        self.lm = Player.objects.create(
            first_name="Left",
            last_name="Mid",
            primary_position=Player.Position.LM,
        )

        self.st = Player.objects.create(
            first_name="Striker",
            last_name="One",
            primary_position=Player.Position.ST,
        )

        self.sub1 = Player.objects.create(
            first_name="Sub",
            last_name="One",
            primary_position=Player.Position.CM,
        )

        self.sub2 = Player.objects.create(
            first_name="Sub",
            last_name="Two",
            primary_position=Player.Position.ST,
        )

        # Create user for submission
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="testpass123",
        )

    def _create_valid_lineup(self):
        """Helper to create a valid 11-player starting lineup."""
        return [
            {
                "player_id": self.gk.id,
                "status": "starter",
                "position": "gk",
                "shirt_number": 1,
                "is_goalkeeper": True,
                "formation_position": 1,
            },
            {
                "player_id": self.cb1.id,
                "status": "starter",
                "position": "cb",
                "shirt_number": 2,
                "formation_position": 2,
            },
            {
                "player_id": self.cb2.id,
                "status": "starter",
                "position": "cb",
                "shirt_number": 3,
                "formation_position": 3,
            },
            {
                "player_id": self.rb.id,
                "status": "starter",
                "position": "rb",
                "shirt_number": 4,
                "formation_position": 4,
            },
            {
                "player_id": self.lb.id,
                "status": "starter",
                "position": "lb",
                "shirt_number": 5,
                "formation_position": 5,
            },
            {
                "player_id": self.cdm.id,
                "status": "starter",
                "position": "cdm",
                "shirt_number": 6,
                "formation_position": 6,
            },
            {
                "player_id": self.cm1.id,
                "status": "starter",
                "position": "cm",
                "shirt_number": 7,
                "formation_position": 7,
            },
            {
                "player_id": self.cm2.id,
                "status": "starter",
                "position": "cm",
                "shirt_number": 8,
                "formation_position": 8,
            },
            {
                "player_id": self.rm.id,
                "status": "starter",
                "position": "rm",
                "shirt_number": 9,
                "formation_position": 9,
            },
            {
                "player_id": self.lm.id,
                "status": "starter",
                "position": "lm",
                "shirt_number": 10,
                "formation_position": 10,
            },
            {
                "player_id": self.st.id,
                "status": "starter",
                "position": "st",
                "shirt_number": 11,
                "is_captain": True,
                "formation_position": 11,
            },
            {
                "player_id": self.sub1.id,
                "status": "substitute",
                "position": "cm",
                "shirt_number": 12,
            },
            {
                "player_id": self.sub2.id,
                "status": "substitute",
                "position": "st",
                "shirt_number": 13,
            },
        ]

    def test_submit_valid_lineup(self):
        """Test submitting a valid lineup."""
        players = self._create_valid_lineup()

        submission = LineupService.submit_lineup(
            tenant=self.tenant,
            match=self.match,
            club=self.home_club,
            players=players,
            formation="4-3-3",
            submitted_by=self.user,
        )

        assert submission is not None
        assert submission.status == LineupSubmission.SubmissionStatus.SUBMITTED
        assert submission.formation == "4-3-3"

        # Check that lineup entries were created
        lineup_entries = MatchLineup.objects.filter(
            tenant=self.tenant,
            match=self.match,
            club=self.home_club,
        )
        assert lineup_entries.count() == 13

    def test_cannot_submit_empty_lineup(self):
        """Test that empty lineup is rejected."""
        with pytest.raises(LineupValidationError):
            LineupService.submit_lineup(
                tenant=self.tenant,
                match=self.match,
                club=self.home_club,
                players=[],
                submitted_by=self.user,
            )

    def test_cannot_submit_wrong_number_of_starters(self):
        """Test that lineups with wrong number of starters are rejected."""
        players = self._create_valid_lineup()
        # Remove one starter
        players = [p for p in players if p["status"] != "starter"][:10]
        players.append({
            "player_id": self.sub1.id,
            "status": "substitute",
            "position": "cm",
            "shirt_number": 12,
        })

        with pytest.raises(LineupValidationError):
            LineupService.submit_lineup(
                tenant=self.tenant,
                match=self.match,
                club=self.home_club,
                players=players,
                submitted_by=self.user,
            )

    def test_cannot_submit_duplicate_players(self):
        """Test that duplicate players in lineup are rejected."""
        players = self._create_valid_lineup()
        # Add duplicate player
        players.append({
            "player_id": self.gk.id,
            "status": "substitute",
            "position": "gk",
            "shirt_number": 20,
        })

        with pytest.raises(LineupValidationError):
            LineupService.submit_lineup(
                tenant=self.tenant,
                match=self.match,
                club=self.home_club,
                players=players,
                submitted_by=self.user,
            )

    def test_cannot_submit_duplicate_shirt_numbers(self):
        """Test that duplicate shirt numbers are rejected."""
        players = self._create_valid_lineup()
        # Set duplicate shirt number
        players[1]["shirt_number"] = 1

        with pytest.raises(LineupValidationError):
            LineupService.submit_lineup(
                tenant=self.tenant,
                match=self.match,
                club=self.home_club,
                players=players,
                submitted_by=self.user,
            )

    def test_cannot_submit_without_goalkeeper(self):
        """Test that lineup without goalkeeper is rejected."""
        players = self._create_valid_lineup()
        # Remove goalkeeper
        players = [p for p in players if not p.get("is_goalkeeper", False)][:11]

        with pytest.raises(LineupValidationError):
            LineupService.submit_lineup(
                tenant=self.tenant,
                match=self.match,
                club=self.home_club,
                players=players,
                submitted_by=self.user,
            )

    def test_cannot_submit_multiple_captains(self):
        """Test that lineup with multiple captains is rejected."""
        players = self._create_valid_lineup()
        # Add second captain
        players[2]["is_captain"] = True

        with pytest.raises(LineupValidationError):
            LineupService.submit_lineup(
                tenant=self.tenant,
                match=self.match,
                club=self.home_club,
                players=players,
                submitted_by=self.user,
            )

    def test_get_lineup_for_club(self):
        """Test retrieving lineup for a club."""
        players = self._create_valid_lineup()

        LineupService.submit_lineup(
            tenant=self.tenant,
            match=self.match,
            club=self.home_club,
            players=players,
            formation="4-3-3",
            submitted_by=self.user,
        )

        lineup = LineupService.get_lineup_for_club(
            tenant=self.tenant,
            match=self.match,
            club=self.home_club,
        )

        assert lineup["club_id"] == str(self.home_club.id)
        assert lineup["formation"] == "4-3-3"
        assert len(lineup["starters"]) == 11
        assert len(lineup["substitutes"]) == 2

    def test_confirm_lineup(self):
        """Test confirming a submitted lineup."""
        players = self._create_valid_lineup()

        submission = LineupService.submit_lineup(
            tenant=self.tenant,
            match=self.match,
            club=self.home_club,
            players=players,
            submitted_by=self.user,
        )

        confirmed = LineupService.confirm_lineup(
            tenant=self.tenant,
            match=self.match,
            club=self.home_club,
            confirmed_by=self.user,
        )

        assert confirmed.status == LineupSubmission.SubmissionStatus.CONFIRMED

    def test_review_lineup_submission(self):
        """Test approving and rejecting a submitted lineup."""
        players = self._create_valid_lineup()

        LineupService.submit_lineup(
            tenant=self.tenant,
            match=self.match,
            club=self.home_club,
            players=players,
            submitted_by=self.user,
        )

        approved = LineupService.review_lineup_submission(
            tenant=self.tenant,
            match=self.match,
            club=self.home_club,
            reviewed_by=self.user,
            approve=True,
            review_notes="Tudo certo.",
        )

        assert approved.status == LineupSubmission.SubmissionStatus.CONFIRMED
        assert approved.review_notes == "Tudo certo."
        assert approved.reviewed_by == self.user

        LineupService.submit_lineup(
            tenant=self.tenant,
            match=self.match,
            club=self.home_club,
            players=players,
            submitted_by=self.user,
        )

        rejected = LineupService.review_lineup_submission(
            tenant=self.tenant,
            match=self.match,
            club=self.home_club,
            reviewed_by=self.user,
            approve=False,
            review_notes="Corrigir o banco.",
        )

        assert rejected.status == LineupSubmission.SubmissionStatus.REJECTED
        assert rejected.review_notes == "Corrigir o banco."

    def test_lock_lineup(self):
        """Test locking a confirmed lineup."""
        players = self._create_valid_lineup()

        LineupService.submit_lineup(
            tenant=self.tenant,
            match=self.match,
            club=self.home_club,
            players=players,
            submitted_by=self.user,
        )

        LineupService.confirm_lineup(
            tenant=self.tenant,
            match=self.match,
            club=self.home_club,
            confirmed_by=self.user,
        )

        locked = LineupService.lock_lineup(
            tenant=self.tenant,
            match=self.match,
            club=self.home_club,
        )

        assert locked.status == LineupSubmission.SubmissionStatus.LOCKED

    def test_cannot_modify_locked_lineup(self):
        """Test that locked lineups cannot be modified."""
        players = self._create_valid_lineup()

        LineupService.submit_lineup(
            tenant=self.tenant,
            match=self.match,
            club=self.home_club,
            players=players,
            submitted_by=self.user,
        )

        LineupService.confirm_lineup(
            tenant=self.tenant,
            match=self.match,
            club=self.home_club,
            confirmed_by=self.user,
        )

        LineupService.lock_lineup(
            tenant=self.tenant,
            match=self.match,
            club=self.home_club,
        )

        # Try to resubmit
        with pytest.raises(LineupAlreadySubmitted):
            LineupService.submit_lineup(
                tenant=self.tenant,
                match=self.match,
                club=self.home_club,
                players=players,
                submitted_by=self.user,
            )

    def test_lock_all_lineups(self):
        """Test locking all lineups for a match."""
        players = self._create_valid_lineup()

        LineupService.submit_lineup(
            tenant=self.tenant,
            match=self.match,
            club=self.home_club,
            players=players,
            submitted_by=self.user,
        )

        LineupService.lock_all_lineups(
            tenant=self.tenant,
            match=self.match,
        )

        submission = LineupSubmission.objects.get(
            match=self.match,
            club=self.home_club,
        )

        assert submission.status == LineupSubmission.SubmissionStatus.LOCKED

    def test_update_player_minutes(self):
        """Test updating player minutes after match."""
        players = self._create_valid_lineup()

        LineupService.submit_lineup(
            tenant=self.tenant,
            match=self.match,
            club=self.home_club,
            players=players,
            submitted_by=self.user,
        )

        # Update minutes for a starter
        entry = LineupService.update_player_minutes(
            tenant=self.tenant,
            match=self.match,
            club=self.home_club,
            player=self.st,
            minutes_played=85,
            substituted_out_minute=75,
        )

        assert entry.minutes_played == 85
        assert entry.substituted_out_minute == 75


@pytest.mark.django_db
class TestMatchReport(TestCase):
    """Test match report and goal recording."""

    def setUp(self):
        """Set up test data."""
        # Create tenant
        self.tenant = Tenant.objects.create(name="Test Org")

        # Create competition
        self.competition = Competition.objects.create(
            tenant=self.tenant,
            name="Test Competition",
            season="2024",
        )

        # Create clubs
        self.home_club = Club.objects.create(
            tenant=self.tenant,
            name="Home Team",
            slug="home-team",
        )

        self.away_club = Club.objects.create(
            tenant=self.tenant,
            name="Away Team",
            slug="away-team",
        )

        # Register clubs in competition
        CompetitionRegistration.objects.create(tenant=self.tenant, competition=self.competition, club=self.home_club)
        CompetitionRegistration.objects.create(tenant=self.tenant, competition=self.competition, club=self.away_club)

        # Create match
        self.match = Match.objects.create(
            tenant=self.tenant,
            competition=self.competition,
            home_club=self.home_club,
            away_club=self.away_club,
            match_date=timezone.now() + timedelta(days=1),
            status=Match.MatchStatus.SCHEDULED,
        )

        # Create players
        self.home_scorer = Player.objects.create(
            first_name="Home",
            last_name="Scorer",
            primary_position=Player.Position.ST,
        )

        self.away_scorer = Player.objects.create(
            first_name="Away",
            last_name="Scorer",
            primary_position=Player.Position.ST,
        )

        self.user = User.objects.create_user(
            email="testuser2@example.com",
            password="testpass123",
        )

    def test_create_match_report(self):
        """Test creating a match report."""
        report = MatchReportService.create_report(
            tenant=self.tenant,
            match=self.match,
            home_score=2,
            away_score=1,
            match_duration=90,
        )

        assert report.home_score == 2
        assert report.away_score == 1
        assert report.match_duration == 90

    def test_record_goal(self):
        """Test recording a goal."""
        goal = MatchReportService.record_goal(
            tenant=self.tenant,
            match=self.match,
            player=self.home_scorer,
            club=self.home_club,
            minute=25,
            goal_type="normal",
        )

        assert goal.player == self.home_scorer
        assert goal.minute == 25
        assert goal.goal_type == "normal"

    def test_get_match_goals(self):
        """Test retrieving goals from a match."""
        MatchReportService.record_goal(
            tenant=self.tenant,
            match=self.match,
            player=self.home_scorer,
            club=self.home_club,
            minute=25,
        )

        MatchReportService.record_goal(
            tenant=self.tenant,
            match=self.match,
            player=self.away_scorer,
            club=self.away_club,
            minute=40,
        )

        goals = MatchReportService.get_match_goals(
            tenant=self.tenant,
            match=self.match,
        )

        assert len(goals) == 2

    def test_get_report_summary(self):
        """Test getting complete report summary."""
        MatchReportService.create_report(
            tenant=self.tenant,
            match=self.match,
            home_score=2,
            away_score=1,
        )

        MatchReportService.record_goal(
            tenant=self.tenant,
            match=self.match,
            player=self.home_scorer,
            club=self.home_club,
            minute=25,
        )

        summary = MatchReportService.get_report_summary(
            tenant=self.tenant,
            match=self.match,
        )

        assert summary["report"]["home_score"] == 2
        assert summary["report"]["away_score"] == 1
        assert len(summary["goals"]["home"]) == 1

