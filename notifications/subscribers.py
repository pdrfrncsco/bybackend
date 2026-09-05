import logging
from typing import Optional

from core.events import Event, EventType, subscribe

from .models import Notification
from players.events.types import (
    PLAYER_REGISTRATION_INVITATION_ACCEPTED,
    PLAYER_REGISTRATION_INVITATION_CREATED,
    PLAYER_REGISTRATION_INVITATION_REJECTED,
    PLAYER_REGISTRATION_REQUEST_APPROVED,
    PLAYER_REGISTRATION_REQUEST_REJECTED,
    PLAYER_REGISTRATION_REQUEST_SUBMITTED,
)

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


def _fanout_match_notification(*, event: Event, notification_type: str) -> None:
    """Create one notification per active tenant member/subscriber."""
    from accounts.models import TenantMembership
    from organizations.models import OrganizationSubscription

    payload = event.payload or {}
    tenant_id = event.tenant_id
    recipient_ids = set(
        TenantMembership.objects.filter(tenant_id=tenant_id, is_active=True)
        .values_list("user_id", flat=True)
    )
    recipient_ids.update(
        OrganizationSubscription.objects.filter(tenant_id=tenant_id, is_active=True)
        .values_list("user_id", flat=True)
    )
    Notification.objects.bulk_create([
        Notification(
            tenant_id=tenant_id,
            recipient_id=recipient_id,
            type=notification_type,
            payload=payload,
        )
        for recipient_id in recipient_ids
    ])


@subscribe(EventType.MATCH_EVENT_CREATED)
def handle_match_event_created(event: Event) -> None:
    _fanout_match_notification(event=event, notification_type=EventType.MATCH_EVENT_CREATED)


@subscribe(EventType.MATCH_FINISHED)
def handle_match_finished(event: Event) -> None:
    _fanout_match_notification(event=event, notification_type=EventType.MATCH_FINISHED)


def _registration_recipients(event: Event, *, to_player: bool = False):
    payload = event.payload or {}
    if to_player:
        return [payload["player_user_id"]] if payload.get("player_user_id") else []
    from clubs.models import ClubMember
    from clubs.constants import ClubMemberRole
    return list(
        ClubMember.objects.filter(
            club_id=payload.get("club_id"), is_active=True,
            role__in=ClubMemberRole.ADMIN_ROLES, user_id__isnull=False,
        ).values_list("user_id", flat=True)
    )


def _create_registration_notifications(event: Event, notification_type: str, *, to_player: bool = False) -> None:
    try:
        payload = event.payload or {}
        recipients = _registration_recipients(event, to_player=to_player)
        for recipient_id in recipients:
            notif = Notification.objects.create(
                tenant_id=event.tenant_id, recipient_id=recipient_id,
                type=notification_type, payload=payload,
            )
            try:
                from .tasks import send_notification_email, send_notification_push
                send_notification_push.delay(notif.id)
                send_notification_email.delay(notif.id)
            except Exception:
                logger.debug("Registration notification delivery unavailable for %s", notif.id)
    except Exception:
        logger.exception("Error handling registration event %s", notification_type)


@subscribe(PLAYER_REGISTRATION_REQUEST_SUBMITTED)
def handle_registration_request_submitted(event: Event) -> None:
    _create_registration_notifications(event, PLAYER_REGISTRATION_REQUEST_SUBMITTED)


@subscribe(PLAYER_REGISTRATION_INVITATION_CREATED)
def handle_registration_invitation_created(event: Event) -> None:
    _create_registration_notifications(event, PLAYER_REGISTRATION_INVITATION_CREATED, to_player=True)


@subscribe(PLAYER_REGISTRATION_REQUEST_APPROVED)
def handle_registration_request_approved(event: Event) -> None:
    _create_registration_notifications(event, PLAYER_REGISTRATION_REQUEST_APPROVED, to_player=True)


@subscribe(PLAYER_REGISTRATION_REQUEST_REJECTED)
def handle_registration_request_rejected(event: Event) -> None:
    _create_registration_notifications(event, PLAYER_REGISTRATION_REQUEST_REJECTED, to_player=True)


@subscribe(PLAYER_REGISTRATION_INVITATION_ACCEPTED)
def handle_registration_invitation_accepted(event: Event) -> None:
    _create_registration_notifications(event, PLAYER_REGISTRATION_INVITATION_ACCEPTED)


@subscribe(PLAYER_REGISTRATION_INVITATION_REJECTED)
def handle_registration_invitation_rejected(event: Event) -> None:
    _create_registration_notifications(event, PLAYER_REGISTRATION_INVITATION_REJECTED)
