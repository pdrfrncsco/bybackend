"""
BOLAYETU — AuthService

Handles all authentication-related business logic.

RULES:
    - All business logic lives here, NOT in views.
    - Views only call these methods and return the result.
    - Services raise domain exceptions on failure.
    - All mutations are wrapped in atomic transactions.
"""

import logging

from django.contrib.auth import authenticate
from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.constants import AccountStatus
from accounts.exceptions import (
    AccountNotFound,
    AccountSuspended,
    AccountNotVerified,
    EmailAlreadyRegistered,
    InvalidCredentials,
    PasswordMismatch,
)
from accounts.models import User
from accounts.selectors import UserSelector

logger = logging.getLogger(__name__)


class AuthService:
    """
    Handles authentication workflows:
        - User registration
        - Login / token generation
        - Logout / token blacklisting
        - Email verification
        - Password reset
    """

    @staticmethod
    @transaction.atomic
    def register(
        *,
        email: str,
        password: str,
        password_confirm: str,
        first_name: str = "",
        last_name: str = "",
        phone: str | None = None,
    ) -> tuple[User, dict]:
        """
        Register a new user and return JWT tokens.

        Args:
            email: User's email address.
            password: Chosen password.
            password_confirm: Password confirmation (must match password).
            first_name: Optional first name.
            last_name: Optional last name.
            phone: Optional phone number.

        Returns:
            Tuple of (User, tokens_dict) where tokens_dict contains
            'access' and 'refresh' keys.

        Raises:
            EmailAlreadyRegistered: If the email is already in use.
            PasswordMismatch: If password and password_confirm differ.
        """
        if password != password_confirm:
            raise PasswordMismatch()

        if UserSelector.email_exists(email=email):
            raise EmailAlreadyRegistered()

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            status=AccountStatus.ACTIVE,  # TODO: change to PENDING_VERIFICATION when email flow is ready
            is_email_verified=True,        # TODO: set to False when email flow is ready
        )

        tokens = AuthService._generate_tokens(user=user)

        logger.info("New user registered: %s", email)

        return user, tokens

    @staticmethod
    def login(*, email: str, password: str) -> tuple[User, dict]:
        """
        Authenticate a user and return JWT tokens.

        Args:
            email: User's email address.
            password: User's password.

        Returns:
            Tuple of (User, tokens_dict).

        Raises:
            InvalidCredentials: If email/password combination is wrong.
            AccountSuspended: If the account is suspended.
            AccountNotVerified: If the email has not been verified.
        """
        user = UserSelector.get_by_email(email=email)

        if user is None:
            raise InvalidCredentials()

        # Django's authenticate checks the password hash
        authenticated_user = authenticate(username=email, password=password)

        if authenticated_user is None:
            raise InvalidCredentials()

        if user.is_suspended:
            raise AccountSuspended()

        if not user.is_email_verified and not user.is_superuser:
            raise AccountNotVerified()


        tokens = AuthService._generate_tokens(user=user)

        logger.info("User logged in: %s", email)

        return user, tokens

    @staticmethod
    def logout(*, refresh_token: str) -> None:
        """
        Blacklist the provided refresh token, effectively logging the user out.

        Args:
            refresh_token: The JWT refresh token string to blacklist.

        Raises:
            InvalidCredentials: If the token is invalid.
        """
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            logger.info("Refresh token blacklisted successfully.")
        except Exception as exc:
            logger.warning("Failed to blacklist token: %s", exc)
            raise InvalidCredentials(
                detail="Invalid or already expired refresh token."
            ) from exc

    @staticmethod
    def _generate_tokens(*, user: User) -> dict:
        """
        Generate access and refresh JWT tokens for a user.

        Args:
            user: The authenticated User instance.

        Returns:
            Dict with 'access' and 'refresh' token strings.
        """
        refresh = RefreshToken.for_user(user)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }
