"""
BOLAYETU — UserService

Handles user profile and account management business logic.
"""

import logging

from django.db import transaction

from accounts.exceptions import IncorrectPassword, AccountNotFound
from accounts.models import User
from accounts.selectors import UserSelector

logger = logging.getLogger(__name__)


class UserService:
    """
    Handles user profile mutations:
        - Profile updates
        - Password changes
        - Account deactivation
    """

    @staticmethod
    @transaction.atomic
    def update_profile(
        *,
        user: User,
        first_name: str | None = None,
        last_name: str | None = None,
        phone: str | None = None,
        language: str | None = None,
        timezone: str | None = None,
    ) -> User:
        """
        Update a user's profile information.

        Only non-None values are updated. This allows partial updates
        without accidentally overwriting existing data.

        Args:
            user: The User instance to update.
            first_name: Optional new first name.
            last_name: Optional new last name.
            phone: Optional new phone number.
            language: Optional new language preference.
            timezone: Optional new timezone preference.

        Returns:
            Updated User instance.
        """
        updated_fields = ["updated_at"]

        if first_name is not None:
            user.first_name = first_name
            updated_fields.append("first_name")

        if last_name is not None:
            user.last_name = last_name
            updated_fields.append("last_name")

        if phone is not None:
            user.phone = phone
            updated_fields.append("phone")

        if language is not None:
            user.language = language
            updated_fields.append("language")

        if timezone is not None:
            user.timezone = timezone
            updated_fields.append("timezone")

        user.save(update_fields=updated_fields)

        logger.info("Profile updated for user: %s", user.email)

        return user

    @staticmethod
    @transaction.atomic
    def change_password(
        *,
        user: User,
        old_password: str,
        new_password: str,
        new_password_confirm: str,
    ) -> User:
        """
        Change a user's password after verifying the current one.

        Args:
            user: The authenticated User instance.
            old_password: The current password for verification.
            new_password: The new password to set.
            new_password_confirm: Must match new_password.

        Returns:
            Updated User instance.

        Raises:
            IncorrectPassword: If old_password does not match current password.
            PasswordMismatch: If new_password != new_password_confirm.
        """
        from accounts.exceptions import PasswordMismatch

        if not user.check_password(old_password):
            raise IncorrectPassword()

        if new_password != new_password_confirm:
            raise PasswordMismatch()

        user.set_password(new_password)
        user.save(update_fields=["password", "updated_at"])

        logger.info("Password changed for user: %s", user.email)

        return user
