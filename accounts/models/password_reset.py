"""
BOLAYETU — PasswordResetToken Model

Stores secure one-time-use tokens for password reset requests.

Flow:
    1. User requests reset → token created and emailed.
    2. User clicks link → token validated and marked used.
    3. Password is updated atomically with token consumption.

Security:
    - Tokens expire after PASSWORD_RESET_TOKEN_EXPIRY minutes.
    - Tokens can only be used once (is_used flag).
    - Token is a random UUID (unguessable).
"""

import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone

from accounts.constants import PASSWORD_RESET_TOKEN_EXPIRY
from common.models import BaseModel


class PasswordResetToken(BaseModel):
    """
    One-time password reset token linked to a User.

    Created when a user requests a password reset. 
    Consumed (marked is_used=True) when the password is successfully changed.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="password_reset_tokens",
        verbose_name="User",
    )
    token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        db_index=True,
        verbose_name="Token",
    )
    expires_at = models.DateTimeField(
        verbose_name="Expires At",
    )
    is_used = models.BooleanField(
        default=False,
        verbose_name="Is Used",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Password Reset Token"
        verbose_name_plural = "Password Reset Tokens"

    def __str__(self) -> str:
        return f"Reset token for {self.user.email} (used={self.is_used})"

    def save(self, *args, **kwargs) -> None:
        """Set expiry on creation if not set."""
        if not self.expires_at:
            from datetime import timedelta
            self.expires_at = timezone.now() + timedelta(
                minutes=PASSWORD_RESET_TOKEN_EXPIRY
            )
        super().save(*args, **kwargs)

    @property
    def is_expired(self) -> bool:
        """Returns True if this token has passed its expiry time."""
        return timezone.now() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Returns True if token can still be used."""
        return not self.is_used and not self.is_expired

    def consume(self) -> None:
        """Mark this token as used. Call after password is changed."""
        self.is_used = True
        self.save(update_fields=["is_used"])
