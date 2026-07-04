"""
BOLAYETU — Club lifecycle domain event tests

Verifies that ClubService.activate()/suspend() publish domain events
(ClubApproved/ClubSuspended) and that notifications subscribers react to
them, end-to-end, without requiring a real Celery broker (in-memory/eager
mode is configured for tests — see config/settings.py TESTING branch).

Uses TransactionTestCase because domain events are dispatched via
transaction.on_commit(), which never fires inside the atomic wrapper used
by the plain TestCase.
"""

from django.test import TransactionTestCase

from clubs.services import ClubService
from core.events import EventType
from core.models import Tenant
from notifications.models import Notification


class ClubLifecycleEventTest(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Org")
        self.club = ClubService.create_club(tenant=self.tenant, name="FC Porto")

    def test_activate_publishes_club_approved_and_creates_notification(self):
        ClubService.activate(club=self.club)

        notif = Notification.objects.filter(type=EventType.CLUB_APPROVED).first()
        self.assertIsNotNone(notif)
        self.assertEqual(notif.payload.get("club_id"), str(self.club.id))
        self.assertEqual(notif.tenant_id, str(self.tenant.id))

    def test_suspend_publishes_club_suspended_and_creates_notification(self):
        ClubService.suspend(club=self.club)

        notif = Notification.objects.filter(type=EventType.CLUB_SUSPENDED).first()
        self.assertIsNotNone(notif)
        self.assertEqual(notif.payload.get("club_id"), str(self.club.id))
