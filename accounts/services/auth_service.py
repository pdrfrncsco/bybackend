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

from django.conf import settings
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.constants import AccountStatus
from accounts.exceptions import (
    AccountNotFound,
    AccountSuspended,
    AccountNotVerified,
    EmailAlreadyRegistered,
    InvalidCredentials,
    InvalidToken,
    PasswordMismatch,
)
from accounts.models import User, PasswordResetToken
from accounts.selectors import UserSelector

logger = logging.getLogger(__name__)


class AuthService:
    """
    Handles authentication workflows:
        - User registration
        - Login / token generation
        - Logout / token blacklisting
        - Password reset (request + confirm)
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
            status=AccountStatus.ACTIVE,
            is_email_verified=True,
        )

        tokens = AuthService._generate_tokens(user=user)
        logger.info("New user registered: %s", email)
        return user, tokens

    @staticmethod
    @transaction.atomic
    def register_organization_owner(
        *,
        email: str,
        password: str,
        password_confirm: str,
        organization_name: str,
        organization_type: str,
        first_name: str = "",
        last_name: str = "",
        phone: str | None = None,
        country: str = "Angola",
        city: str = "",
    ) -> tuple[User, dict, "Tenant"]:
        """
        Register a user and bootstrap a pending organization with owner membership.

        Single atomic transaction — rolls back user if organization creation fails.
        """
        from core.models import Tenant
        from organizations.services import OrganizationService

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
            status=AccountStatus.ACTIVE,
            is_email_verified=True,
        )
        tokens = AuthService._generate_tokens(user=user)
        logger.info("New user registered: %s", email)

        tenant = OrganizationService.create_organization_with_owner(
            user=user,
            name=organization_name,
            org_type=organization_type,
            country=country,
            city=city or None,
        )

        return user, tokens, tenant

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
        Blacklist the provided refresh token.

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
    @transaction.atomic
    def request_password_reset(*, email: str) -> None:
        """
        Initiate a password reset flow by sending a reset email.

        Always returns successfully even if the email is not registered,
        to prevent email enumeration attacks.

        Args:
            email: Email address to send the reset link to.
        """
        user = UserSelector.get_by_email(email=email)

        if user is None:
            # Do NOT reveal whether the email exists or not
            logger.info("Password reset requested for unknown email: %s", email)
            return

        if user.is_suspended:
            logger.warning(
                "Password reset requested for suspended account: %s", email
            )
            # Still silently succeed — don't reveal account status
            return

        # Invalidate any existing unused tokens for this user
        PasswordResetToken.objects.filter(user=user, is_used=False).update(is_used=True)

        # Create new reset token
        reset_token = PasswordResetToken.objects.create(user=user)

        # Build reset URL
        reset_url = (
            f"{settings.FRONTEND_URL}/reset-password"
            f"?token={reset_token.token}"
            f"&email={user.email}"
        )

        # Send email (console backend in dev, SMTP in prod)
        try:
            subject = "Bolayetu — Recuperar Palavra-passe"
            message = (
                f"Olá {user.full_name},\n\n"
                f"Recebemos um pedido para redefinir a sua palavra-passe.\n\n"
                f"Clique no link abaixo para criar uma nova palavra-passe:\n"
                f"{reset_url}\n\n"
                f"Este link expira em 60 minutos.\n\n"
                f"Se não solicitou este pedido, ignore este email.\n\n"
                f"— Equipa Bolayetu"
            )
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            logger.info("Password reset email sent to: %s", email)
        except Exception as exc:
            logger.error("Failed to send password reset email to %s: %s", email, exc)
            raise

    @staticmethod
    @transaction.atomic
    def confirm_password_reset(
        *,
        token: str,
        new_password: str,
        new_password_confirm: str,
    ) -> None:
        """
        Validate a reset token and update the user's password.

        Args:
            token: The UUID token from the reset link.
            new_password: The new password to set.
            new_password_confirm: Must match new_password.

        Raises:
            PasswordMismatch: If new_password != new_password_confirm.
            InvalidToken: If the token is invalid, expired, or already used.
        """
        if new_password != new_password_confirm:
            raise PasswordMismatch()

        try:
            reset_token = PasswordResetToken.objects.select_related("user").get(
                token=token
            )
        except PasswordResetToken.DoesNotExist:
            raise InvalidToken()

        if not reset_token.is_valid:
            raise InvalidToken()

        # Update password
        user = reset_token.user
        user.set_password(new_password)
        user.save(update_fields=["password", "updated_at"])

        # Consume token
        reset_token.consume()

        logger.info("Password reset confirmed for user: %s", user.email)

    @staticmethod
    def _generate_tokens(*, user: User) -> dict:
        """Generate access and refresh JWT tokens for a user."""
        refresh = RefreshToken.for_user(user)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }
