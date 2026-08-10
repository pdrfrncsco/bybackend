from datetime import timedelta
from django.utils import timezone

from players.models import PlayerInvite


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
        return invite

    @staticmethod
    def redeem_invite(token):
        try:
            invite = PlayerInvite.objects.get(token=token)
        except PlayerInvite.DoesNotExist:
            return None
        if invite.is_expired() or invite.redeemed:
            return None
        invite.redeemed = True
        invite.redeemed_at = timezone.now()
        invite.save(update_fields=['redeemed', 'redeemed_at'])
        return invite
