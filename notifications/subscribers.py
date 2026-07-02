import logging
from typing import Optional

from core.events import subscribe, Event
from .models import Notification

logger = logging.getLogger(__name__)


@subscribe("ClubApproved")
def handle_club_approved(event: Event) -> None:
    """Create notifications when a club is approved.

    Creates a Notification record and enqueues delivery tasks.
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
            type="ClubApproved",
            payload={"club_id": club_id},
        )

        # Enqueue delivery via tasks module (Celery if available)
        try:
            from .tasks import send_notification_push, send_notification_email
            # Best-effort: enqueue both push and email
            send_notification_push.delay(notif.id)
            send_notification_email.delay(notif.id)
            logger.info("Enqueued notification delivery for %s", notif.id)
        except Exception:
            # Fallback to sync calls
            try:
                from .tasks import send_notification_push
                from .tasks import send_notification_email
                send_notification_push(notif.id)
                send_notification_email(notif.id)
            except Exception:
                logger.debug("Notification delivery not available for %s", notif.id)

    except Exception:
        logger.exception("Error handling ClubApproved event: %s", event)
