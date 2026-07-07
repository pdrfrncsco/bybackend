import logging

import requests
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger(__name__)
from core.metrics import notifications_failed_total, notifications_sent_total


class NotificationDeliveryError(Exception):
    """Raised for transient delivery failures that are worth retrying.

    Permanent conditions (e.g. no recipient configured) are NOT raised as
    this exception — they are terminal and retrying would not help.
    """


def send_notification_email_sync(notification_id: int) -> None:
    """Synchronous email sender using Django's send_mail.

    Uses settings.EMAIL_* configuration. Updates Notification.status on
    success or failure.

    Raises:
        NotificationDeliveryError: on a transient send failure, so the
            calling Celery task can retry. Does NOT raise when there is
            simply no recipient to send to (permanent, not retryable).
    """
    from .models import Notification

    try:
        notif = Notification.objects.get(id=notification_id)
    except Notification.DoesNotExist:
        logger.debug("Notification %s not found for email delivery", notification_id)
        return

    subject = f"[{notif.type}] Notification"
    body = notif.payload and str(notif.payload) or ""
    recipient_list = []
    if notif.recipient_id:
        try:
            recipient_list = [notif.recipient.email]
        except Exception:
            recipient_list = []

    if not recipient_list:
        # No recipient configured — permanent condition, do not retry.
        Notification.objects.filter(id=notification_id).update(status=Notification.STATUS_FAILED)
        notifications_failed_total.inc()
        logger.debug("Email notification %s had no recipients", notification_id)
        return

    try:
        send_count = send_mail(
            subject,
            body,
            getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@localhost"),
            recipient_list,
            fail_silently=False,
        )
    except Exception as exc:
        logger.exception("Failed to send email for notification %s", notification_id)
        Notification.objects.filter(id=notification_id).update(status=Notification.STATUS_FAILED)
        notifications_failed_total.inc()
        raise NotificationDeliveryError(str(exc)) from exc

    if send_count:
        Notification.objects.filter(id=notification_id).update(
            status=Notification.STATUS_SENT, delivered_at=timezone.now()
        )
        notifications_sent_total.inc()
        logger.info("Email notification %s sent to %s", notification_id, recipient_list)
    else:
        Notification.objects.filter(id=notification_id).update(status=Notification.STATUS_FAILED)
        notifications_failed_total.inc()
        logger.warning("Email notification %s reported zero deliveries", notification_id)


def send_notification_push_sync(notification_id: int) -> None:
    """Simple push delivery via HTTP webhook if NOTIFICATION_PUSH_ENDPOINT is set,
    otherwise marks the notification as sent (best-effort, no-op channel).

    Raises:
        NotificationDeliveryError: on a transient delivery failure (network
            error or non-2xx response), so the calling Celery task can retry.
    """
    from .models import Notification

    try:
        notif = Notification.objects.get(id=notification_id)
    except Notification.DoesNotExist:
        logger.debug("Notification %s not found for push delivery", notification_id)
        return

    endpoint = getattr(settings, "NOTIFICATION_PUSH_ENDPOINT", None)
    payload = notif.payload or {}

    if not endpoint:
        # No push endpoint configured — mark as sent (best-effort) and log
        Notification.objects.filter(id=notification_id).update(
            status=Notification.STATUS_SENT, delivered_at=timezone.now()
        )
        logger.info("No push endpoint configured; marked notification %s as sent", notification_id)
        return

    try:
        resp = requests.post(endpoint, json={"notification_id": notification_id, "payload": payload}, timeout=5)
    except Exception as exc:
        logger.exception("Push delivery failed for notification %s", notification_id)
        Notification.objects.filter(id=notification_id).update(status=Notification.STATUS_FAILED)
        notifications_failed_total.inc()
        raise NotificationDeliveryError(str(exc)) from exc

    if 200 <= resp.status_code < 300:
        Notification.objects.filter(id=notification_id).update(
            status=Notification.STATUS_SENT, delivered_at=timezone.now()
        )
        notifications_sent_total.inc()
        logger.info("Push notification %s delivered to %s", notification_id, endpoint)
    else:
        Notification.objects.filter(id=notification_id).update(status=Notification.STATUS_FAILED)
        notifications_failed_total.inc()
        logger.warning("Push delivery returned status %s for notification %s", resp.status_code, notification_id)
        raise NotificationDeliveryError(f"HTTP {resp.status_code} from push endpoint")


# Celery tasks are optional; try to import celery's app and define tasks if available.
#
# Retry policy: notification delivery is user-facing and its outcome is
# persisted on Notification.status (pending/sent/failed), so these tasks are
# the "persist + retry" category described in
# docs/01-architecture/10_EVENTS_AND_WORKFLOWS.md §24. Transient failures
# (NotificationDeliveryError) are retried with backoff; permanent failures
# (e.g. no recipient) are marked failed immediately without retry.
try:
    from celery import shared_task
    from celery.exceptions import Retry

    from .models import Notification

    @shared_task(bind=True, max_retries=3, default_retry_delay=30, name="notifications.send_notification_email")
    def send_notification_email(self, notification_id: int) -> None:
        logger.info("send_notification_email task for %s", notification_id)
        try:
            send_notification_email_sync(notification_id)
        except NotificationDeliveryError as exc:
            try:
                raise self.retry(exc=exc)
            except Retry:
                raise
            except Exception:
                # Retries exhausted — already persisted as FAILED in DB.
                logger.error("Email notification %s failed after max retries", notification_id)

    @shared_task(bind=True, max_retries=3, default_retry_delay=30, name="notifications.send_notification_push")
    def send_notification_push(self, notification_id: int) -> None:
        logger.info("send_notification_push task for %s", notification_id)
        try:
            send_notification_push_sync(notification_id)
        except NotificationDeliveryError as exc:
            try:
                raise self.retry(exc=exc)
            except Retry:
                raise
            except Exception:
                # Retries exhausted — already persisted as FAILED in DB.
                logger.error("Push notification %s failed after max retries", notification_id)
except Exception:
    # Celery not available — provide wrappers that call sync implementations.
    # No retry infrastructure without Celery; the failure is still persisted
    # on Notification.status by the *_sync functions.
    def send_notification_email(notification_id: int) -> None:
        try:
            send_notification_email_sync(notification_id)
        except NotificationDeliveryError:
            logger.debug("Email delivery failed for notification %s (no retry backend)", notification_id)

    def send_notification_push(notification_id: int) -> None:
        try:
            send_notification_push_sync(notification_id)
        except NotificationDeliveryError:
            logger.debug("Push delivery failed for notification %s (no retry backend)", notification_id)
