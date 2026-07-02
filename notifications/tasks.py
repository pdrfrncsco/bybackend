import logging
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import requests

logger = logging.getLogger(__name__)
from core.metrics import notifications_sent_total, notifications_failed_total


def send_notification_email_sync(notification_id: int) -> None:
    """Synchronous email sender using Django's send_mail.

    Uses settings.EMAIL_* configuration. Updates Notification.status on success or failure.
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

    try:
        # send_mail returns number of successfully delivered messages
        send_count = send_mail(
            subject,
            body,
            getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@localhost"),
            recipient_list,
            fail_silently=False,
        ) if recipient_list else 0

        if send_count:
            Notification.objects.filter(id=notification_id).update(status=Notification.STATUS_SENT, delivered_at=timezone.now())
            notifications_sent_total.inc()
            logger.info("Email notification %s sent to %s", notification_id, recipient_list)
        else:
            # no recipients configured — mark as failed
            Notification.objects.filter(id=notification_id).update(status=Notification.STATUS_FAILED)
            notifications_failed_total.inc()
            logger.debug("Email notification %s had no recipients", notification_id)
    except Exception:
        logger.exception("Failed to send email for notification %s", notification_id)
        Notification.objects.filter(id=notification_id).update(status=Notification.STATUS_FAILED)
        notifications_failed_total.inc()


def send_notification_push_sync(notification_id: int) -> None:
    """Simple push delivery via HTTP webhook if NOTIFICATION_PUSH_ENDPOINT is set, otherwise log.

    Updates Notification.status accordingly.
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
        Notification.objects.filter(id=notification_id).update(status=Notification.STATUS_SENT, delivered_at=timezone.now())
        logger.info("No push endpoint configured; marked notification %s as sent", notification_id)
        return

    try:
        resp = requests.post(endpoint, json={"notification_id": notification_id, "payload": payload}, timeout=5)
        if resp.status_code >= 200 and resp.status_code < 300:
            Notification.objects.filter(id=notification_id).update(status=Notification.STATUS_SENT, delivered_at=timezone.now())
            notifications_sent_total.inc()
            logger.info("Push notification %s delivered to %s", notification_id, endpoint)
        else:
            Notification.objects.filter(id=notification_id).update(status=Notification.STATUS_FAILED)
            notifications_failed_total.inc()
            logger.warning("Push delivery returned status %s for notification %s", resp.status_code, notification_id)
    except Exception:
        logger.exception("Push delivery failed for notification %s", notification_id)
        Notification.objects.filter(id=notification_id).update(status=Notification.STATUS_FAILED)
        notifications_failed_total.inc()


# Celery tasks are optional; try to import celery's app and define tasks if available
try:
    from celery import shared_task
    from .models import Notification

    @shared_task
    def send_notification_email(notification_id: int) -> None:
        logger.info("send_notification_email task for %s", notification_id)
        try:
            send_notification_email_sync(notification_id)
        except Exception:
            logger.exception("Failed to send notification email %s", notification_id)

    @shared_task
    def send_notification_push(notification_id: int) -> None:
        logger.info("send_notification_push task for %s", notification_id)
        try:
            send_notification_push_sync(notification_id)
        except Exception:
            logger.exception("Failed to send notification push %s", notification_id)
except Exception:
    # Celery not available — provide wrappers that call sync implementations
    def send_notification_email(notification_id: int) -> None:
        send_notification_email_sync(notification_id)

    def send_notification_push(notification_id: int) -> None:
        send_notification_push_sync(notification_id)
