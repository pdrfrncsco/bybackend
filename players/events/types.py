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

# Phase 3 events (Professional)
PLAYER_CONTRACT_SIGNED = "players.player.contract.signed"
PLAYER_CONTRACT_RENEWED = "players.player.contract.renewed"
PLAYER_CONTRACT_TERMINATED = "players.player.contract.terminated"
PLAYER_TRANSFER_REQUESTED = "players.player.transfer.requested"
PLAYER_RELEASED = "players.player.released"
PLAYER_LOAN_STARTED = "players.player.loan.started"
PLAYER_LOAN_ENDED = "players.player.loan.ended"
PLAYER_AGENT_LINKED = "players.player.agent.linked"
PLAYER_AGENT_UNLINKED = "players.player.agent.unlinked"
PLAYER_TRAINING_ADDED = "players.player.training.added"
PLAYER_TRAINING_VERIFIED = "players.player.training.verified"


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


def publish_player_contract_signed(contract_id: str, player_id: str, club_id: str, start_date: str, end_date: str, user_id: Optional[str] = None, tenant_id: Optional[str] = None) -> None:
    payload = {
        "contract_id": str(contract_id),
        "player_id": str(player_id),
        "club_id": str(club_id),
        "start_date": start_date,
        "end_date": end_date,
    }
    _publish(PLAYER_CONTRACT_SIGNED, payload, user_id=user_id, tenant_id=tenant_id)


def publish_player_contract_terminated(contract_id: str, player_id: str, club_id: str, reason: str, user_id: Optional[str] = None, tenant_id: Optional[str] = None) -> None:
    payload = {
        "contract_id": str(contract_id),
        "player_id": str(player_id),
        "club_id": str(club_id),
        "reason": reason,
    }
    _publish(PLAYER_CONTRACT_TERMINATED, payload, user_id=user_id, tenant_id=tenant_id)


def publish_player_transferred(player_id: str, from_club_id: Optional[str], to_club_id: str, transfer_fee: Optional[float] = None, user_id: Optional[str] = None, tenant_id: Optional[str] = None) -> None:
    payload = {
        "player_id": str(player_id),
        "from_club_id": str(from_club_id) if from_club_id else None,
        "to_club_id": str(to_club_id),
        "transfer_fee": transfer_fee,
    }
    _publish(PLAYER_TRANSFERRED, payload, user_id=user_id, tenant_id=tenant_id)


def publish_player_released(player_id: str, from_club_id: str, reason: str, user_id: Optional[str] = None, tenant_id: Optional[str] = None) -> None:
    payload = {
        "player_id": str(player_id),
        "from_club_id": str(from_club_id),
        "reason": reason,
    }
    _publish(PLAYER_RELEASED, payload, user_id=user_id, tenant_id=tenant_id)


def publish_player_loan_started(player_id: str, from_club_id: str, to_club_id: str, loan_start_date: str, loan_end_date: str, user_id: Optional[str] = None, tenant_id: Optional[str] = None) -> None:
    payload = {
        "player_id": str(player_id),
        "from_club_id": str(from_club_id),
        "to_club_id": str(to_club_id),
        "loan_start_date": loan_start_date,
        "loan_end_date": loan_end_date,
    }
    _publish(PLAYER_LOAN_STARTED, payload, user_id=user_id, tenant_id=tenant_id)


def publish_player_loan_ended(player_id: str, loan_club_id: str, parent_club_id: Optional[str], end_date: str, user_id: Optional[str] = None, tenant_id: Optional[str] = None) -> None:
    payload = {
        "player_id": str(player_id),
        "loan_club_id": str(loan_club_id),
        "parent_club_id": str(parent_club_id) if parent_club_id else None,
        "end_date": end_date,
    }
    _publish(PLAYER_LOAN_ENDED, payload, user_id=user_id, tenant_id=tenant_id)


def publish_player_agent_linked(player_id: str, agent_id: str, relationship_id: str, user_id: Optional[str] = None, tenant_id: Optional[str] = None) -> None:
    payload = {
        "player_id": str(player_id),
        "agent_id": str(agent_id),
        "relationship_id": str(relationship_id),
    }
    _publish(PLAYER_AGENT_LINKED, payload, user_id=user_id, tenant_id=tenant_id)


def publish_player_agent_unlinked(player_id: str, agent_id: str, reason: Optional[str] = None, user_id: Optional[str] = None, tenant_id: Optional[str] = None) -> None:
    payload = {
        "player_id": str(player_id),
        "agent_id": str(agent_id),
        "reason": reason,
    }
    _publish(PLAYER_AGENT_UNLINKED, payload, user_id=user_id, tenant_id=tenant_id)


def publish_player_training_added(player_id: str, training_id: str, club_id: Optional[str], academy_name: Optional[str], start_date: str, category: str, user_id: Optional[str] = None, tenant_id: Optional[str] = None) -> None:
    payload = {
        "player_id": str(player_id),
        "training_id": str(training_id),
        "club_id": str(club_id) if club_id else None,
        "academy_name": academy_name,
        "start_date": start_date,
        "category": category,
    }
    _publish(PLAYER_TRAINING_ADDED, payload, user_id=user_id, tenant_id=tenant_id)


def publish_player_training_verified(training_id: str, player_id: str, verified_by_id: str, user_id: Optional[str] = None, tenant_id: Optional[str] = None) -> None:
    payload = {
        "training_id": str(training_id),
        "player_id": str(player_id),
        "verified_by_id": str(verified_by_id),
    }
    _publish(PLAYER_TRAINING_VERIFIED, payload, user_id=user_id, tenant_id=tenant_id)
