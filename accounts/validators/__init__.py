"""
BOLAYETU — Accounts Validators

Reusable validation functions for the accounts domain.
These validators are used by serializers and services.
"""

import re
from typing import Any

from django.core.exceptions import ValidationError

from accounts.constants import MIN_PASSWORD_LENGTH, MAX_PASSWORD_LENGTH


def validate_password_strength(password: str) -> None:
    """
    Validate that a password meets the Bolayetu security requirements.

    Rules:
        - Minimum 8 characters
        - Maximum 128 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character

    Args:
        password: The password string to validate.

    Raises:
        ValidationError: If the password does not meet the requirements.
    """
    errors = []

    if len(password) < MIN_PASSWORD_LENGTH:
        errors.append(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long.")

    if len(password) > MAX_PASSWORD_LENGTH:
        errors.append(f"Password must not exceed {MAX_PASSWORD_LENGTH} characters.")

    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter.")

    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter.")

    if not re.search(r"\d", password):
        errors.append("Password must contain at least one digit.")

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\;'/`~]", password):
        errors.append("Password must contain at least one special character.")

    if errors:
        raise ValidationError(errors)


def validate_phone_number(phone: str) -> None:
    """
    Validate that a phone number is in a valid format.

    Accepts international format with optional country code.

    Args:
        phone: The phone number string to validate.

    Raises:
        ValidationError: If the phone number format is invalid.
    """
    cleaned = re.sub(r"[\s\-\(\)]", "", phone)

    if not re.match(r"^\+?[1-9]\d{6,14}$", cleaned):
        raise ValidationError(
            "Enter a valid phone number. Include country code if international (e.g. +244923000000)."
        )


def validate_username_format(username: str) -> None:
    """
    Validate that a username meets format requirements.

    Rules:
        - 3 to 30 characters
        - Only letters, digits, underscores and hyphens
        - Cannot start or end with underscore or hyphen

    Args:
        username: The username string to validate.

    Raises:
        ValidationError: If the username format is invalid.
    """
    if len(username) < 3:
        raise ValidationError("Username must be at least 3 characters long.")

    if len(username) > 30:
        raise ValidationError("Username must not exceed 30 characters.")

    if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9_\-]*[a-zA-Z0-9]$", username):
        raise ValidationError(
            "Username may only contain letters, digits, underscores and hyphens, "
            "and cannot start or end with an underscore or hyphen."
        )
