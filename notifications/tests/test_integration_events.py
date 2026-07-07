from django.test import TestCase, TransactionTestCase
from django.db import transaction

from core.events import Event, publish_event
from notifications.models import Notification


class EventsIntegrationTest(TransactionTestCase):
    reset_sequences = True

    def test_club_approved_creates_notification(self):
        # publish event inside atomic block so on_commit handlers run after commit
        with transaction.atomic():
            evt = Event(type="ClubApproved", payload={"club_id": "club-123", "recipient_id": None}, origin="tests")
            publish_event(evt)
        # after the atomic block commit, subscribers should have run and created Notification
        notif = Notification.objects.filter(type="ClubApproved").first()
        self.assertIsNotNone(notif)
        self.assertEqual(notif.payload.get("club_id"), "club-123")
