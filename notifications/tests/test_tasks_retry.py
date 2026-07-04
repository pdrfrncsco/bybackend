"""
BOLAYETU — Notification delivery retry tests

Verifies that transient delivery failures are retried with backoff and
that the final outcome is always persisted on Notification.status, per the
persistence/retry policy documented in
docs/01-architecture/10_EVENTS_AND_WORKFLOWS.md (§24) and
notifications/tasks.py.

These tests never touch a real broker or network: Celery runs in eager
in-memory mode during tests (see config/settings.py TESTING branch), and
the actual email/HTTP calls are mocked.

Note: tasks are invoked with `.apply(..., throw=False)` rather than
`.delay()`. Test settings set CELERY_TASK_EAGER_PROPAGATES=True (to
surface unexpected task errors quickly elsewhere in the suite), but that
setting also short-circuits Celery's own eager retry-recursion loop. Using
`throw=False` for these specific calls lets self.retry() recurse
synchronously as it would on a real worker, without disabling the safer
default globally.
"""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from notifications.models import Notification
from notifications.tasks import send_notification_email, send_notification_push

User = get_user_model()


# Celery's own retry-recursion in eager mode reads task_eager_propagates on
# every recursive apply() call, so it must be disabled for the duration of
# these tests (globally, not just on the outermost call) to let self.retry()
# actually loop instead of raising through .delay()/.apply() immediately.
@override_settings(CELERY_TASK_EAGER_PROPAGATES=False)
class EmailDeliveryRetryTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="retry@bolayetu.com", password="SecurePass123!")

    @patch("notifications.tasks.send_mail")
    def test_transient_failure_retries_then_marks_failed(self, mock_send_mail):
        mock_send_mail.side_effect = Exception("smtp temporarily unavailable")
        notif = Notification.objects.create(type="Test", payload={}, recipient=self.user)

        send_notification_email.delay(notif.id)

        notif.refresh_from_db()
        self.assertEqual(notif.status, Notification.STATUS_FAILED)
        # 1 initial attempt + 3 retries (max_retries=3), all synchronous (no real delay/broker)
        self.assertEqual(mock_send_mail.call_count, 4)

    @patch("notifications.tasks.send_mail")
    def test_recovers_on_retry(self, mock_send_mail):
        """A transient failure that succeeds on retry should end as SENT."""
        mock_send_mail.side_effect = [Exception("smtp temporarily unavailable"), 1]
        notif = Notification.objects.create(type="Test", payload={}, recipient=self.user)

        send_notification_email.delay(notif.id)

        notif.refresh_from_db()
        self.assertEqual(notif.status, Notification.STATUS_SENT)
        self.assertEqual(mock_send_mail.call_count, 2)

    def test_no_recipient_fails_immediately_without_retry(self):
        """Permanent conditions (no recipient) must not be retried."""
        notif = Notification.objects.create(type="Test", payload={})

        with patch("notifications.tasks.send_mail") as mock_send_mail:
            send_notification_email.delay(notif.id)
            mock_send_mail.assert_not_called()

        notif.refresh_from_db()
        self.assertEqual(notif.status, Notification.STATUS_FAILED)


@override_settings(CELERY_TASK_EAGER_PROPAGATES=False)
class PushDeliveryRetryTest(TestCase):
    @patch("notifications.tasks.requests.post")
    def test_transient_failure_retries_then_marks_failed(self, mock_post):
        mock_post.side_effect = Exception("network unreachable")
        notif = Notification.objects.create(type="Test", payload={})

        with self.settings(NOTIFICATION_PUSH_ENDPOINT="https://push.example.com/notify"):
            send_notification_push.delay(notif.id)

        notif.refresh_from_db()
        self.assertEqual(notif.status, Notification.STATUS_FAILED)
        self.assertEqual(mock_post.call_count, 4)

    def test_no_endpoint_configured_marks_sent_without_network_call(self):
        """Absence of a push channel is best-effort success, not a failure."""
        notif = Notification.objects.create(type="Test", payload={})

        with patch("notifications.tasks.requests.post") as mock_post:
            send_notification_push.delay(notif.id)
            mock_post.assert_not_called()

        notif.refresh_from_db()
        self.assertEqual(notif.status, Notification.STATUS_SENT)
