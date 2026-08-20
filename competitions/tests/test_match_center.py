"""
Tests for Phase 4 — Match Center (MatchEvent service and API).
"""

from datetime import datetime, timezone

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from accounts.models import User
from accounts.models.membership import TenantMembership
from clubs.models import Club
from core.models import Tenant
from players.models import Player
from competitions.models import Competition, CompetitionRegistration, Match, MatchEvent, MatchReport, Standing, MatchClockAction
from competitions.services.match_event_service import (
    MatchEventService, InvalidMatchEventData, MatchEventNotFound
)
from competitions.services.match_service import MatchService, InvalidMatchTransition


def make_tenant(name="Liga Angola"):
    return Tenant.objects.create(name=name, slug=name.lower().replace(" ", "-"))


def make_user(tenant, email="admin@test.com", role="admin"):
    user = User.objects.create_user(email=email, password="pass1234", is_active=True)
    user.status = "active"
    user.save(update_fields=["status"])
    TenantMembership.objects.create(tenant=tenant, user=user, role=role, is_active=True)
    return user


def make_club(tenant, name="Clube A"):
    return Club.objects.create(tenant=tenant, name=name, slug=name.lower().replace(" ", "-"))


def make_competition(tenant, name="Liga 2026"):
    return Competition.objects.create(
        tenant=tenant, name=name, competition_type="league", season="2025/26", status="active"
    )


def make_match(tenant, competition, home, away, round_number=1):
    return Match.objects.create(
        tenant=tenant,
        competition=competition,
        home_club=home,
        away_club=away,
        round_number=round_number,
        match_date=datetime(2026, 8, 1, 16, 0, tzinfo=timezone.utc),
        status=Match.MatchStatus.SCHEDULED,
    )


def make_player(first_name="Paulo", last_name="Silva"):
    return Player.objects.create(
        first_name=first_name,
        last_name=last_name,
        date_of_birth="2000-01-01",
        nationality="Angola",
        primary_position="fw",
    )


class MatchEventServiceTestCase(TestCase):
    def setUp(self):
        self.tenant = make_tenant()
        self.home = make_club(self.tenant, "Sport Luanda")
        self.away = make_club(self.tenant, "Petro Luanda")
        self.comp = make_competition(self.tenant)
        self.match = make_match(self.tenant, self.comp, self.home, self.away)
        self.player = make_player()

    def test_add_goal_updates_score(self):
        """Adding a goal event recalculates the match score."""
        MatchEventService.add_event(
            tenant=self.tenant,
            match=self.match,
            club=self.home,
            event_type=MatchEvent.EventType.GOAL,
            minute=30,
            player=self.player,
        )
        self.match.refresh_from_db()
        self.assertEqual(self.match.home_score, 1)
        self.assertEqual(self.match.away_score, 0)

    def test_add_two_goals_correct_score(self):
        """Two goals for home → 2–0."""
        for minute in [20, 55]:
            MatchEventService.add_event(
                tenant=self.tenant, match=self.match,
                club=self.home, event_type=MatchEvent.EventType.GOAL,
                minute=minute,
            )
        self.match.refresh_from_db()
        self.assertEqual(self.match.home_score, 2)
        self.assertEqual(self.match.away_score, 0)

    def test_own_goal_credits_opponent(self):
        """An own goal by home club credits away team."""
        MatchEventService.add_event(
            tenant=self.tenant, match=self.match,
            club=self.home, event_type=MatchEvent.EventType.OWN_GOAL,
            minute=45,
        )
        self.match.refresh_from_db()
        self.assertEqual(self.match.home_score, 0)
        self.assertEqual(self.match.away_score, 1)

    def test_remove_goal_recalculates_score(self):
        """Deleting a goal event re-zeroes the score."""
        ev = MatchEventService.add_event(
            tenant=self.tenant, match=self.match,
            club=self.home, event_type=MatchEvent.EventType.GOAL,
            minute=10,
        )
        MatchEventService.remove_event(tenant=self.tenant, event_id=str(ev.id))
        self.match.refresh_from_db()
        self.assertEqual(self.match.home_score, 0)
        self.assertEqual(self.match.away_score, 0)

    def test_non_goal_event_does_not_change_score(self):
        """Yellow card does not affect score."""
        MatchEventService.add_event(
            tenant=self.tenant, match=self.match,
            club=self.home, event_type=MatchEvent.EventType.YELLOW_CARD,
            minute=25, player=self.player,
        )
        self.match.refresh_from_db()
        self.assertIsNone(self.match.home_score)
        self.assertIsNone(self.match.away_score)

    def test_add_event_invalid_minute_raises(self):
        """Minute > 120 raises InvalidMatchEventData."""
        with self.assertRaises(InvalidMatchEventData):
            MatchEventService.add_event(
                tenant=self.tenant, match=self.match,
                club=self.home, event_type=MatchEvent.EventType.GOAL,
                minute=999,
            )

    def test_add_event_invalid_event_type_raises(self):
        """Unknown event_type raises InvalidMatchEventData."""
        with self.assertRaises(InvalidMatchEventData):
            MatchEventService.add_event(
                tenant=self.tenant, match=self.match,
                club=self.home, event_type="flying_kick",
                minute=10,
            )

    def test_remove_nonexistent_event_raises(self):
        """Removing non-existent event raises MatchEventNotFound."""
        import uuid
        with self.assertRaises(MatchEventNotFound):
            MatchEventService.remove_event(
                tenant=self.tenant, event_id=str(uuid.uuid4())
            )

    def test_list_events_for_match(self):
        """list_events_for_match returns only this match's events ordered by minute."""
        MatchEventService.add_event(
            tenant=self.tenant, match=self.match,
            club=self.home, event_type=MatchEvent.EventType.YELLOW_CARD,
            minute=33, player=self.player,
        )
        MatchEventService.add_event(
            tenant=self.tenant, match=self.match,
            club=self.away, event_type=MatchEvent.EventType.GOAL,
            minute=67,
        )
        events = MatchEventService.list_events_for_match(
            tenant=self.tenant, match_id=str(self.match.id)
        )
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].minute, 33)
        self.assertEqual(events[1].minute, 67)

    def test_idempotent_event_retry_returns_original(self):
        first = MatchEventService.add_event(
            tenant=self.tenant, match=self.match, club=self.home,
            event_type=MatchEvent.EventType.GOAL, minute=10,
            idempotency_key="client-retry-1",
        )
        second = MatchEventService.add_event(
            tenant=self.tenant, match=self.match, club=self.home,
            event_type=MatchEvent.EventType.GOAL, minute=10,
            idempotency_key="client-retry-1",
        )
        self.assertEqual(first.id, second.id)
        self.assertEqual(MatchEvent.objects.filter(match=self.match).count(), 1)


class MatchLifecycleServiceTestCase(TestCase):
    def setUp(self):
        self.tenant = make_tenant()
        self.home = make_club(self.tenant, "Lifecycle Home")
        self.away = make_club(self.tenant, "Lifecycle Away")
        self.comp = make_competition(self.tenant)
        self.match = make_match(self.tenant, self.comp, self.home, self.away)

    def test_valid_lifecycle_transitions(self):
        MatchService.transition_match(
            tenant=self.tenant, match_id=str(self.match.id), status="pre_match"
        )
        MatchService.transition_match(
            tenant=self.tenant, match_id=str(self.match.id), status="live",
            current_period="first_half",
        )
        MatchService.transition_match(
            tenant=self.tenant, match_id=str(self.match.id), status="finished",
            current_period="fulltime",
        )
        self.match.refresh_from_db()
        self.assertEqual(self.match.status, Match.MatchStatus.FINISHED)

    def test_invalid_lifecycle_jump_is_rejected(self):
        with self.assertRaises(InvalidMatchTransition):
            MatchService.transition_match(
                tenant=self.tenant, match_id=str(self.match.id), status="finished"
            )

    def test_archiving_before_finished_is_rejected(self):
        with self.assertRaises(InvalidMatchTransition):
            MatchService.transition_match(
                tenant=self.tenant, match_id=str(self.match.id), status="archived"
            )

    def test_clock_actions_record_periods_and_audit(self):
        MatchService.transition_match(tenant=self.tenant, match_id=str(self.match.id), status="pre_match")
        MatchService.apply_clock_action(tenant=self.tenant, match_id=str(self.match.id), action="start_first_half")
        MatchService.apply_clock_action(tenant=self.tenant, match_id=str(self.match.id), action="end_first_half")
        MatchService.apply_clock_action(tenant=self.tenant, match_id=str(self.match.id), action="start_second_half")
        self.match.refresh_from_db()
        self.assertEqual(self.match.current_period, Match.MatchPeriod.SECOND_HALF)
        self.assertTrue(self.match.clock_running)
        self.assertEqual(MatchClockAction.objects.filter(match=self.match).count(), 3)

    def test_clock_rejects_stale_version(self):
        from competitions.services.match_service import InvalidClockAction
        MatchService.transition_match(tenant=self.tenant, match_id=str(self.match.id), status="pre_match")
        MatchService.apply_clock_action(tenant=self.tenant, match_id=str(self.match.id), action="start_first_half")
        with self.assertRaises(InvalidClockAction):
            MatchService.apply_clock_action(
                tenant=self.tenant,
                match_id=str(self.match.id),
                action="end_first_half",
                expected_version=0,
            )

    def test_extra_time_and_penalty_shootout_flow(self):
        self.comp.config = {"extraTimeOnDraw": True, "penaltiesOnDraw": True}
        self.comp.save(update_fields=["config"])
        self.match.status = Match.MatchStatus.LIVE
        self.match.current_period = Match.MatchPeriod.SECOND_HALF
        self.match.home_score = 1
        self.match.away_score = 1
        self.match.clock_running = True
        self.match.save(update_fields=["status", "current_period", "home_score", "away_score", "clock_running"])
        MatchService.apply_clock_action(tenant=self.tenant, match_id=str(self.match.id), action="start_extra_time")
        MatchService.apply_clock_action(tenant=self.tenant, match_id=str(self.match.id), action="end_extra_first_half")
        MatchService.apply_clock_action(tenant=self.tenant, match_id=str(self.match.id), action="start_extra_second_half")
        MatchService.apply_clock_action(tenant=self.tenant, match_id=str(self.match.id), action="start_penalties")
        match = MatchService.apply_clock_action(
            tenant=self.tenant,
            match_id=str(self.match.id),
            action="finish_match",
            home_penalty_score=5,
            away_penalty_score=4,
        )
        self.assertEqual(match.status, Match.MatchStatus.FINISHED)
        self.assertEqual(match.home_penalty_score, 5)
        self.assertEqual(match.away_penalty_score, 4)


class MatchCenterAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.tenant = make_tenant()
        self.admin = make_user(self.tenant)
        self.home = make_club(self.tenant, "Benfica Luanda")
        self.away = make_club(self.tenant, "Sagrada Esperança")
        self.comp = make_competition(self.tenant)
        self.match = make_match(self.tenant, self.comp, self.home, self.away)
        self.player = make_player()

    def _auth(self):
        from rest_framework_simplejwt.tokens import RefreshToken
        token = RefreshToken.for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

    def test_list_events_public(self):
        """GET events endpoint is accessible without authentication."""
        url = f"/api/v1/competitions/{self.comp.id}/matches/{self.match.id}/events/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"], [])

    def test_add_goal_event_admin(self):
        """POST a goal event as admin → 201, score recalculated."""
        self._auth()
        url = f"/api/v1/competitions/{self.comp.id}/matches/{self.match.id}/events/"
        payload = {
            "event_type": "goal",
            "minute": 42,
            "club": str(self.home.id),
            "player": str(self.player.id),
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.match.refresh_from_db()
        self.assertEqual(self.match.home_score, 1)

    def test_add_event_unauthenticated_forbidden(self):
        """POST without auth → 401/403."""
        url = f"/api/v1/competitions/{self.comp.id}/matches/{self.match.id}/events/"
        response = self.client.post(url, {"event_type": "goal", "minute": 10, "club": str(self.home.id)}, format="json")
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_delete_event_admin(self):
        """DELETE a goal event as admin → score reset to 0."""
        self._auth()
        ev = MatchEventService.add_event(
            tenant=self.tenant, match=self.match,
            club=self.home, event_type=MatchEvent.EventType.GOAL,
            minute=10,
        )
        url = f"/api/v1/competitions/{self.comp.id}/matches/{self.match.id}/events/{ev.id}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.match.refresh_from_db()
        self.assertEqual(self.match.home_score, 0)

    def test_player_stats_public(self):
        """GET /stats/ endpoint is public and returns aggregated player stats."""
        MatchEventService.add_event(
            tenant=self.tenant, match=self.match,
            club=self.home, event_type=MatchEvent.EventType.GOAL,
            minute=15, player=self.player,
        )
        url = f"/api/v1/competitions/{self.comp.id}/stats/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        stats = response.data["data"]
        self.assertEqual(len(stats), 1)
        self.assertEqual(stats[0]["goals"], 1)


class MatchCenterRBACAPITestCase(TestCase):
    """Role matrix for live operations, approval and archival."""

    def setUp(self):
        self.client = APIClient()
        self.tenant = make_tenant("RBAC League")
        self.admin = make_user(self.tenant, "rbac-admin@test.com", "admin")
        self.manager = make_user(self.tenant, "rbac-manager@test.com", "manager")
        self.member = make_user(self.tenant, "rbac-member@test.com", "member")
        self.home = make_club(self.tenant, "RBAC Home")
        self.away = make_club(self.tenant, "RBAC Away")
        self.comp = make_competition(self.tenant, "RBAC Competition")
        self.match = make_match(self.tenant, self.comp, self.home, self.away)

    def _auth_as(self, user):
        from rest_framework_simplejwt.tokens import RefreshToken
        token = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

    def _transition(self, status_value):
        return self.client.patch(
            f"/api/v1/competitions/matches/{self.match.id}/transition/",
            {"status": status_value}, format="json",
        )

    def test_manager_can_open_pre_match_and_start_live(self):
        self._auth_as(self.manager)
        self.assertEqual(self._transition("pre_match").status_code, status.HTTP_200_OK)
        self.assertEqual(self._transition("live").status_code, status.HTTP_200_OK)

    def test_member_cannot_operate_live_match(self):
        self._auth_as(self.member)
        response = self._transition("pre_match")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_manager_cannot_archive_match(self):
        self.match.status = Match.MatchStatus.FINISHED
        self.match.save(update_fields=["status"])
        self._auth_as(self.manager)
        response = self._transition("archived")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_archive_finished_match(self):
        self.match.status = Match.MatchStatus.FINISHED
        self.match.save(update_fields=["status"])
        self._auth_as(self.admin)
        response = self._transition("archived")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.match.refresh_from_db()
        self.assertEqual(self.match.status, Match.MatchStatus.ARCHIVED)

    def test_manager_can_submit_but_not_finalize_report(self):
        url = f"/api/v1/competitions/matches/{self.match.id}/report/create/"
        payload = {"home_score": 1, "away_score": 0, "match_duration": 90}

        self._auth_as(self.manager)
        submitted = self.client.post(url, payload, format="json")
        self.assertIn(submitted.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])

        rejected = self.client.post(url, {**payload, "status": "finalized"}, format="json")
        self.assertEqual(rejected.status_code, status.HTTP_403_FORBIDDEN)

        self._auth_as(self.admin)
        approved = self.client.post(url, {**payload, "status": "finalized"}, format="json")
        self.assertIn(approved.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        self.assertEqual(approved.data["status"], MatchReport.ReportStatus.FINALIZED)
