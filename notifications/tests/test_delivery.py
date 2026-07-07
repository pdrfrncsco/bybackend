from django.test import TestCase, override_settings
from django.core import mail
from notifications.models import Notification
from notifications.tasks import send_notification_email_sync


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', DEFAULT_FROM_EMAIL='test@example.com')
class DeliveryTest(TestCase):
    def test_send_notification_email_sync_updates_status_and_sends_email(self):
        notif = Notification.objects.create(type='TestEmail', payload={'msg': 'hello'})
        send_notification_email_sync(notif.id)

        notif.refresh_from_db()
        self.assertEqual(notif.status, Notification.STATUS_FAILED)  # no recipient -> failed

        # Now create one with recipient (User model may be accounts.User)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.create_user(email='user@example.com', password='pass')
        notif2 = Notification.objects.create(type='TestEmail', payload={'msg': 'hi'}, recipient=user)
        send_notification_email_sync(notif2.id)
        notif2.refresh_from_db()
        self.assertEqual(notif2.status, Notification.STATUS_SENT)
        # Check that an email was sent
        self.assertEqual(len(mail.outbox), 1)
