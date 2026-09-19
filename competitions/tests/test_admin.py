from django.test import TestCase, RequestFactory
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model

from django.utils import timezone
from core.models import Tenant
from clubs.models import Club
from competitions.models import Competition, Match, MatchEvent, MatchClockAction
from competitions.admin import MatchAdmin, MatchEventAdmin, MatchClockActionAdmin, _is_cascade_deletion

User = get_user_model()


class MockSuperUser:
    is_active = True
    is_staff = True
    is_superuser = True

    def has_perm(self, perm, obj=None):
        return True


class MockStaffUser:
    is_active = True
    is_staff = True
    is_superuser = False

    def has_perm(self, perm, obj=None):
        return perm in ("competitions.delete_match", "competitions.change_match")


class CompetitionsAdminTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.site = AdminSite()
        self.tenant = Tenant.objects.create(name="FAF", slug="faf", status=Tenant.TenantStatus.ACTIVE)
        self.club1 = Club.objects.create(tenant=self.tenant, name="Club A", slug="club-a")
        self.club2 = Club.objects.create(tenant=self.tenant, name="Club B", slug="club-b")
        self.competition = Competition.objects.create(
            tenant=self.tenant,
            name="Girabola",
            competition_type="league",
            season="2025/2026",
        )
        self.match = Match.objects.create(
            tenant=self.tenant,
            competition=self.competition,
            home_club=self.club1,
            away_club=self.club2,
            match_date=timezone.now(),
        )
        self.event = MatchEvent.objects.create(
            tenant=self.tenant,
            match=self.match,
            club=self.club1,
            event_type=MatchEvent.EventType.GOAL,
            minute=10,
        )
        self.clock_action = MatchClockAction.objects.create(
            tenant=self.tenant,
            match=self.match,
            action="start",
            status_before="scheduled",
            status_after="in_progress",
        )
        self.event_admin = MatchEventAdmin(MatchEvent, self.site)
        self.clock_admin = MatchClockActionAdmin(MatchClockAction, self.site)
        self.match_admin = MatchAdmin(Match, self.site)

    def test_superuser_has_delete_permission_everywhere(self):
        req = self.factory.post("/admin/competitions/matchevent/")
        req.user = MockSuperUser()
        self.assertTrue(self.event_admin.has_delete_permission(req, self.event))
        self.assertTrue(self.clock_admin.has_delete_permission(req, self.clock_action))

    def test_staff_cannot_delete_standalone_events(self):
        req = self.factory.post("/admin/competitions/matchevent/")
        req.user = MockStaffUser()
        self.assertFalse(self.event_admin.has_delete_permission(req, self.event))

        req_clock = self.factory.post("/admin/competitions/matchclockaction/")
        req_clock.user = MockStaffUser()
        self.assertFalse(self.clock_admin.has_delete_permission(req_clock, self.clock_action))

    def test_cascade_delete_allowed_when_deleting_match(self):
        # Request is on the match changelist or match delete page
        req_match = self.factory.post(f"/admin/competitions/match/{self.match.id}/delete/")
        req_match.user = MockStaffUser()

        # Both admins should grant delete permission during cascade from match
        self.assertTrue(self.event_admin.has_delete_permission(req_match, self.event))
        self.assertTrue(self.clock_admin.has_delete_permission(req_match, self.clock_action))

    def test_cascade_helper(self):
        req_match = self.factory.post("/admin/competitions/match/")
        req_match.user = MockStaffUser()
        self.assertTrue(_is_cascade_deletion(req_match, "matchevent"))
        self.assertTrue(_is_cascade_deletion(req_match, "matchclockaction"))

        req_event = self.factory.post("/admin/competitions/matchevent/")
        req_event.user = MockStaffUser()
        self.assertFalse(_is_cascade_deletion(req_event, "matchevent"))

    def test_get_deleted_objects_has_no_missing_permissions(self):
        from django.contrib.admin.utils import get_deleted_objects
        from django.contrib import admin

        req = self.factory.post(f"/admin/competitions/match/{self.match.id}/delete/")
        req.user = MockSuperUser()

        deleted_objects, model_count, perms_needed, protected = get_deleted_objects(
            [self.match], req, admin.site
        )
        # Previously perms_needed would contain {"Match Event", "Match Clock Action"}
        self.assertEqual(len(perms_needed), 0)
        self.assertEqual(len(protected), 0)
