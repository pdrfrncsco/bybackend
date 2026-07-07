import logging
from typing import Optional

from core.events import Event, EventType, subscribe

from .models import Notification

logger = logging.getLogger(__name__)


def _create_club_notification(*, event: Event, notification_type: str) -> Optional[Notification]:
    """Shared logic for club lifecycle events (approved/suspended).

    Creates a Notification record and enqueues delivery tasks. Best-effort:
    failures are logged and never propagate back to the publisher.
    """
    try:
        payload = event.payload or {}
        club_id = payload.get("club_id")
        tenant_id = event.tenant_id
        # recipient could be passed in payload (e.g., club admin user id)
        recipient_id = payload.get("recipient_id")

        notif = Notification.objects.create(
            tenant_id=tenant_id,
            recipient_id=recipient_id,
            type=notification_type,
            payload={"club_id": club_id, "club_name": payload.get("club_name")},
        )

        # Enqueue delivery via tasks module (Celery if available)
        try:
            from .tasks import send_notification_email, send_notification_push

            # Best-effort: enqueue both push and email
            send_notification_push.delay(notif.id)
            send_notification_email.delay(notif.id)
            logger.info("Enqueued notification delivery for %s", notif.id)
        except Exception:
            # Fallback to sync calls
            try:
                from .tasks import send_notification_email, send_notification_push

                send_notification_push(notif.id)
                send_notification_email(notif.id)
            except Exception:
                logger.debug("Notification delivery not available for %s", notif.id)

        return notif

    except Exception:
        logger.exception("Error handling %s event: %s", notification_type, event)
        return None


@subscribe(EventType.CLUB_APPROVED)
def handle_club_approved(event: Event) -> None:
    """Create a notification when a club is approved."""
    _create_club_notification(event=event, notification_type=EventType.CLUB_APPROVED)


@subscribe(EventType.CLUB_SUSPENDED)
def handle_club_suspended(event: Event) -> None:
    """Create a notification when a club is suspended."""
    _create_club_notification(event=event, notification_type=EventType.CLUB_SUSPENDED)
