"""
BOLAYETU — AuthService and UserService Tests
"""

from django.test import TestCase

from accounts.services.auth_service import AuthService
from accounts.services.user_service import UserService
from accounts.models import User
from accounts.exceptions import (
    EmailAlreadyRegistered,
    PasswordMismatch,
    InvalidCredentials,
    AccountSuspended,
    IncorrectPassword,
)


class AuthServiceTest(TestCase):
    """Tests authentication business services."""

    def test_registration_success(self):
        """AuthService.register successfully creates a user and returns tokens."""
        user, tokens = AuthService.register(
            email="register@bolayetu.com",
            password="SecurePass123!",
            password_confirm="SecurePass123!",
            first_name="Pedro",
            last_name="Francisco",
        )
        self.assertEqual(user.email, "register@bolayetu.com")
        self.assertEqual(user.first_name, "Pedro")
        self.assertIn("access", tokens)
        self.assertIn("refresh", tokens)

    def test_registration_password_mismatch(self):
        """AuthService.register raises PasswordMismatch when confirms do not match."""
        with self.assertRaises(PasswordMismatch):
            AuthService.register(
                email="mismatch@bolayetu.com",
                password="SecurePass123!",
                password_confirm="WrongConfirm123!",
            )

    def test_registration_duplicate_email(self):
        """AuthService.register raises EmailAlreadyRegistered when email is taken."""
        AuthService.register(
            email="duplicate@bolayetu.com",
            password="SecurePass123!",
            password_confirm="SecurePass123!",
        )
        with self.assertRaises(EmailAlreadyRegistered):
            AuthService.register(
                email="duplicate@bolayetu.com",
                password="OtherSecurePass123!",
                password_confirm="OtherSecurePass123!",
            )

    def test_login_success(self):
        """AuthService.login returns user and tokens for valid credentials."""
        user, _ = AuthService.register(
            email="login@bolayetu.com",
            password="SecurePass123!",
            password_confirm="SecurePass123!",
        )
        # Verify user is verified/active in test setup
        logged_user, tokens = AuthService.login(
            email="login@bolayetu.com",
            password="SecurePass123!",
        )
        self.assertEqual(logged_user, user)
        self.assertIn("access", tokens)

    def test_login_invalid_credentials(self):
        """AuthService.login raises InvalidCredentials on incorrect email or password."""
        AuthService.register(
            email="wrong@bolayetu.com",
            password="SecurePass123!",
            password_confirm="SecurePass123!",
        )
        with self.assertRaises(InvalidCredentials):
            AuthService.login(email="wrong@bolayetu.com", password="IncorrectPassword123!")

        with self.assertRaises(InvalidCredentials):
            AuthService.login(email="nonexistent@bolayetu.com", password="SecurePass123!")

    def test_login_suspended_account(self):
        """AuthService.login raises AccountSuspended if user account is suspended."""
        user, _ = AuthService.register(
            email="suspended@bolayetu.com",
            password="SecurePass123!",
            password_confirm="SecurePass123!",
        )
        user.suspend()
        with self.assertRaises(AccountSuspended):
            AuthService.login(email="suspended@bolayetu.com", password="SecurePass123!")


class UserServiceTest(TestCase):
    """Tests user management business services."""

    def setUp(self):
        self.user, _ = AuthService.register(
            email="user@bolayetu.com",
            password="SecurePass123!",
            password_confirm="SecurePass123!",
        )

    def test_update_profile_partial(self):
        """UserService.update_profile updates only specified fields."""
        UserService.update_profile(
            user=self.user,
            first_name="NovoNome",
            phone="923000000"
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "NovoNome")
        self.assertEqual(self.user.phone, "923000000")
        self.assertEqual(self.user.last_name, "")  # Unmodified

    def test_change_password_success(self):
        """UserService.change_password updates password with correct old password match."""
        UserService.change_password(
            user=self.user,
            old_password="SecurePass123!",
            new_password="NewSecurePass321!",
            new_password_confirm="NewSecurePass321!"
        )
        # Authentication should succeed with new password
        user_logged, _ = AuthService.login(email="user@bolayetu.com", password="NewSecurePass321!")
        self.assertEqual(user_logged, self.user)

    def test_change_password_incorrect_old(self):
        """UserService.change_password raises IncorrectPassword if old password is incorrect."""
        with self.assertRaises(IncorrectPassword):
            UserService.change_password(
                user=self.user,
                old_password="WrongOldPassword123!",
                new_password="NewSecurePass321!",
                new_password_confirm="NewSecurePass321!"
            )
