import uuid
from django.db import models
from django.utils import timezone
from common.models import BaseModel


class PlayerInvite(BaseModel):
    """Represents an invitation to a player to create/link a profile.

    Token can be used by the frontend to pre-fill data and create a linked player account.
    """

    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    email = models.EmailField()
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)
    invited_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="player_invites",
    )
    club = models.ForeignKey(
        "clubs.Club",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="player_invites",
    )
    expires_at = models.DateTimeField(null=True, blank=True)
    redeemed = models.BooleanField(default=False)
    redeemed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Player Invite"
        verbose_name_plural = "Player Invites"

    def __str__(self) -> str:
        return f"Invite {self.email} ({self.token})"

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return timezone.now() > self.expires_at
