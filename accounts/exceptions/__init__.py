"""
BOLAYETU — Accounts Exceptions

Domain-specific exceptions for the accounts module.
All exceptions should be caught in services and translated
into appropriate HTTP responses by the views.
"""

from rest_framework import status
from rest_framework.exceptions import APIException


class AccountException(APIException):
    """Base exception for all accounts domain errors."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "An accounts error occurred."
    default_code = "accounts_error"


class InvalidCredentials(AccountException):
    """Raised when email/password combination is invalid."""

    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "Invalid email or password."
    default_code = "invalid_credentials"


class AccountNotFound(AccountException):
    """Raised when a user account does not exist."""

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Account not found."
    default_code = "account_not_found"


class AccountSuspended(AccountException):
    """Raised when a user attempts to authenticate with a suspended account."""

    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "This account has been suspended. Please contact support."
    default_code = "account_suspended"


class AccountNotVerified(AccountException):
    """Raised when a user attempts to authenticate without verifying their email."""

    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "Please verify your email address before logging in."
    default_code = "account_not_verified"


class EmailAlreadyRegistered(AccountException):
    """Raised when attempting to register with an email that already exists."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = "An account with this email address already exists."
    default_code = "email_already_registered"


class InvalidToken(AccountException):
    """Raised when a provided token (reset, verification) is invalid or expired."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "The provided token is invalid or has expired."
    default_code = "invalid_token"


class PasswordMismatch(AccountException):
    """Raised when password confirmation does not match the password."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Passwords do not match."
    default_code = "password_mismatch"


class IncorrectPassword(AccountException):
    """Raised when the provided current password is incorrect."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "The current password is incorrect."
    default_code = "incorrect_password"


class MembershipAlreadyExists(AccountException):
    """Raised when attempting to add a user to a tenant they already belong to."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = "This user is already a member of this organization."
    default_code = "membership_already_exists"


class MembershipNotFound(AccountException):
    """Raised when a tenant membership record does not exist."""

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Membership not found."
    default_code = "membership_not_found"
