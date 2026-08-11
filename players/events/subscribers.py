import logging
from typing import Optional

from core.events import Event, subscribe

from notifications.models import Notification

from players.events import PLAYER_INVITE_CREATED, PLAYER_INVITE_REDEEMED

logger = logging.getLogger(__name__)


def _create_invite_notification(event: Event, notification_type: str) -> Optional[Notification]:
    """Create a Notification record for invite events and enqueue delivery tasks.

    Best-effort: failures are logged and do not propagate back to publisher.
    """
    try:
        payload = event.payload or {}
        tenant_id = event.tenant_id

        # Build a notification payload; keep the original event payload for context
        notif = Notification.objects.create(
            tenant_id=tenant_id,
            type=notification_type,
            payload=payload,
        )

        # Enqueue delivery via notifications.tasks (Celery if available)
        try:
            from notifications.tasks import send_notification_email, send_notification_push

            send_notification_push.delay(notif.id)
            send_notification_email.delay(notif.id)
            logger.info("Enqueued invite notification delivery for %s", notif.id)
        except Exception:
            # Fallback to sync calls
            try:
                from notifications.tasks import send_notification_email, send_notification_push

                send_notification_push(notif.id)
                send_notification_email(notif.id)
                logger.info("Delivered invite notification (sync) for %s", notif.id)
            except Exception:
                logger.debug("Notification delivery not available for %s", notif.id)

        return notif

    except Exception:
        logger.exception("Error handling invite event: %s", event)
        return None


@subscribe(PLAYER_INVITE_CREATED)
def handle_invite_created(event: Event) -> None:
    _create_invite_notification(event=event, notification_type=PLAYER_INVITE_CREATED)


@subscribe(PLAYER_INVITE_REDEEMED)
def handle_invite_redeemed(event: Event) -> None:
    _create_invite_notification(event=event, notification_type=PLAYER_INVITE_REDEEMED)
