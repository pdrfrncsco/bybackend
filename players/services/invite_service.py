from datetime import timedelta
from django.utils import timezone

from players.models import PlayerInvite
from players.events.types import publish_invite_created, publish_invite_redeemed


class PlayerInviteService:
    @staticmethod
    def create_invite(email: str, first_name: str = '', last_name: str = '', invited_by=None, club=None, expires_days: int = 14) -> PlayerInvite:
        expires_at = timezone.now() + timedelta(days=expires_days) if expires_days else None
        invite = PlayerInvite.objects.create(
            email=email,
            first_name=first_name or '',
            last_name=last_name or '',
            invited_by=invited_by,
            club=club,
            expires_at=expires_at,
        )
        # Stub: here we would enqueue email sending with the token link
        # Best-effort publish domain event for invite created
        try:
            publish_invite_created(
                invite.id,
                invite.email,
                invite.token,
                club_id=getattr(club, "id", None) if club else None,
                invited_by_id=getattr(invited_by, "id", None) if invited_by else None,
                expires_at=invite.expires_at.isoformat() if invite.expires_at else None,
            )
        except Exception:
            # Do not fail invite creation on event publish errors
            pass
        return invite

    @staticmethod
    def redeem_invite(token, redeemed_by_user=None):
        try:
            invite = PlayerInvite.objects.get(token=token)
        except PlayerInvite.DoesNotExist:
            return None
        if invite.is_expired() or invite.redeemed:
            return None
        invite.redeemed = True
        invite.redeemed_at = timezone.now()
        invite.save(update_fields=['redeemed', 'redeemed_at'])

        # Best-effort publish domain event for invite redeemed
        try:
            publish_invite_redeemed(
                invite.id,
                invite.email,
                invite.token,
                redeemed_at=invite.redeemed_at.isoformat() if invite.redeemed_at else None,
                redeemed_by_user_id=getattr(redeemed_by_user, "id", None) if redeemed_by_user else None,
                tenant_id=getattr(invite, "club", None) and getattr(getattr(invite, "club", None), "tenant_id", None),
            )
        except Exception:
            pass

        return invite
