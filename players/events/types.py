"""Players domain event types and helper publishers.

This file defines canonical event type strings and small helper functions to
publish domain events via core.events.dispatcher.publish_event.
"""
from typing import Optional, Dict, Any

from core.events.base import Event
from core.events.dispatcher import publish_event

# Existing canonical event type strings (keep backwards-compatible names)
PLAYER_CREATED = "players.player.created"
PLAYER_ONBOARDING_COMPLETED = "players.player.onboarding_completed"
PLAYER_VERIFIED = "players.player.verified"
PLAYER_DOCUMENT_UPLOADED = "players.player.document.uploaded"
PLAYER_DOCUMENT_VERIFIED = "players.player.document.verified"
PLAYER_STATUS_CHANGED = "players.player.status.changed"
PLAYER_REGISTRATION_CREATED = "players.player.registration.created"
PLAYER_TRANSFERRED = "players.player.transferred"

# Phase 2 additions
PLAYER_CAREER_UPDATED = "players.player.career.updated"
PLAYER_SEASON_STATISTICS_UPDATED = "players.player.season_statistics.updated"
PLAYER_INVITE_CREATED = "players.player.invite.created"
PLAYER_INVITE_REDEEMED = "players.player.invite.redeemed"


def _publish(event_type: str, payload: Dict[str, Any], origin: Optional[str] = None, tenant_id: Optional[str] = None, user_id: Optional[str] = None) -> None:
    event = Event(type=event_type, payload=payload, origin=origin, tenant_id=tenant_id, user_id=user_id)
    publish_event(event)


def publish_player_created(player_id: str, slug: str, full_name: str, user_id: Optional[str] = None) -> None:
    payload = {"player_id": str(player_id), "slug": slug, "full_name": full_name}
    _publish(PLAYER_CREATED, payload, user_id=user_id)


def publish_player_registration_created(registration_id: str, player_id: str, club_id: str, competition_id: Optional[str], joined_date: str, user_id: Optional[str] = None, tenant_id: Optional[str] = None) -> None:
    payload = {
        "registration_id": str(registration_id),
        "player_id": str(player_id),
        "club_id": str(club_id),
        "competition_id": str(competition_id) if competition_id else None,
        "joined_date": str(joined_date),
    }
    _publish(PLAYER_REGISTRATION_CREATED, payload, user_id=user_id, tenant_id=tenant_id)


def publish_player_career_updated(player_id: str, seasons_affected: list, user_id: Optional[str] = None) -> None:
    payload = {"player_id": str(player_id), "seasons": seasons_affected}
    _publish(PLAYER_CAREER_UPDATED, payload, user_id=user_id)


def publish_player_season_statistics_updated(player_id: str, seasons_affected: list, user_id: Optional[str] = None, tenant_id: Optional[str] = None) -> None:
    payload = {"player_id": str(player_id), "seasons": seasons_affected}
    _publish(PLAYER_SEASON_STATISTICS_UPDATED, payload, user_id=user_id, tenant_id=tenant_id)


def publish_invite_created(invite_id: str, email: str, token: str, club_id: Optional[str] = None, invited_by_id: Optional[str] = None, expires_at: Optional[str] = None, user_id: Optional[str] = None, tenant_id: Optional[str] = None) -> None:
    payload = {
        "invite_id": str(invite_id),
        "email": email,
        "token": token,
        "club_id": str(club_id) if club_id else None,
        "invited_by_id": str(invited_by_id) if invited_by_id else None,
        "expires_at": expires_at,
    }
    _publish(PLAYER_INVITE_CREATED, payload, user_id=user_id, tenant_id=tenant_id)


def publish_invite_redeemed(invite_id: str, email: str, token: str, redeemed_at: str, redeemed_by_user_id: Optional[str] = None, tenant_id: Optional[str] = None) -> None:
    payload = {
        "invite_id": str(invite_id),
        "email": email,
        "token": token,
        "redeemed_at": redeemed_at,
        "redeemed_by_user_id": str(redeemed_by_user_id) if redeemed_by_user_id else None,
    }
    _publish(PLAYER_INVITE_REDEEMED, payload, tenant_id=tenant_id)
