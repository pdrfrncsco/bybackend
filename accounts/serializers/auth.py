"""
BOLAYETU — Authentication Serializers

Serializers for auth endpoints: register, login, logout, change-password.
These handle INPUT validation only — no business logic.
"""

from rest_framework import serializers

from accounts.constants import LanguageCode
from accounts.validators import validate_password_strength
from organizations.constants import OrganizationType


class RegisterSerializer(serializers.Serializer):
    """
    Validates registration input.

    Used for: POST /api/v1/auth/register/
    """

    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )
    first_name = serializers.CharField(max_length=150, default="", allow_blank=True)
    last_name = serializers.CharField(max_length=150, default="", allow_blank=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True, default=None)

    def validate_password(self, value: str) -> str:
        """Apply domain password strength rules."""
        from django.core.exceptions import ValidationError as DjangoValidationError
        try:
            validate_password_strength(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)
        return value

    def validate(self, attrs: dict) -> dict:
        """Verify password and confirmation match."""
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )
        return attrs


class RegisterOrganizationSerializer(RegisterSerializer):
    """
    Validates organization owner registration input.

    Used for: POST /api/v1/auth/register/organization/
    """

    organization_name = serializers.CharField(max_length=255)
    organization_type = serializers.ChoiceField(
        choices=OrganizationType.CHOICES,
        default=OrganizationType.FEDERATION,
    )
    country = serializers.CharField(max_length=100, default="Angola", required=False)
    city = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")


class LoginSerializer(serializers.Serializer):
    """
    Validates login credentials.

    Used for: POST /api/v1/auth/login/
    """

    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )


class LogoutSerializer(serializers.Serializer):
    """
    Validates logout request.

    Used for: POST /api/v1/auth/logout/
    """

    refresh = serializers.CharField(
        help_text="The refresh token to blacklist."
    )


class ChangePasswordSerializer(serializers.Serializer):
    """
    Validates password change request.

    Used for: POST /api/v1/auth/change-password/
    """

    old_password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )
    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )

    def validate_new_password(self, value: str) -> str:
        """Apply domain password strength rules."""
        from django.core.exceptions import ValidationError as DjangoValidationError
        try:
            validate_password_strength(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)
        return value

    def validate(self, attrs: dict) -> dict:
        """Verify new password and confirmation match."""
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "Passwords do not match."}
            )
        return attrs


class TokenResponseSerializer(serializers.Serializer):
    """
    Schema-only serializer for token response documentation.
    Used only for OpenAPI schema generation.
    """

    access = serializers.CharField()
    refresh = serializers.CharField()


class ForgotPasswordSerializer(serializers.Serializer):
    """
    Validates forgot password request.

    Used for: POST /api/v1/auth/forgot-password/
    """

    email = serializers.EmailField(
        help_text="Email address associated with the account."
    )


class ResetPasswordSerializer(serializers.Serializer):
    """
    Validates password reset with token.

    Used for: POST /api/v1/auth/reset-password/
    """

    token = serializers.UUIDField(
        help_text="Reset token received by email."
    )
    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )

    def validate_new_password(self, value: str) -> str:
        """Apply domain password strength rules."""
        from django.core.exceptions import ValidationError as DjangoValidationError
        try:
            validate_password_strength(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)
        return value

    def validate(self, attrs: dict) -> dict:
        """Verify new password and confirmation match."""
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "Passwords do not match."}
            )
        return attrs
