"""
BOLAYETU — Accounts Auth Views
Authentication and Token Management
"""

from rest_framework import serializers, status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema

from accounts.services.auth_service import AuthService
from accounts.serializers.auth import (
    RegisterSerializer,
    RegisterOrganizationSerializer,
    LoginSerializer,
    LogoutSerializer,
    TokenResponseSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
)
from accounts.serializers.user import UserSerializer
from organizations.serializers import OrganizationSerializer
from common.responses import success_response, created_response


class RegisterView(APIView):
    """Register a new user account. Returns access and refresh JWT tokens."""

    permission_classes = [AllowAny]

    @extend_schema(
        tags=["auth"],
        request=RegisterSerializer,
        responses={201: TokenResponseSerializer},
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user, tokens = AuthService.register(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
            password_confirm=serializer.validated_data["password_confirm"],
            first_name=serializer.validated_data.get("first_name", ""),
            last_name=serializer.validated_data.get("last_name", ""),
            phone=serializer.validated_data.get("phone"),
        )

        return created_response(
            data={
                "access": tokens["access"],
                "refresh": tokens["refresh"],
                "user": UserSerializer(user).data,
            },
            message="User registered successfully.",
        )


class RegisterOrganizationView(APIView):
    """Register a new organization owner. Creates user, tenant and owner membership."""

    permission_classes = [AllowAny]

    @extend_schema(
        tags=["auth"],
        request=RegisterOrganizationSerializer,
        responses={201: TokenResponseSerializer},
    )
    def post(self, request):
        serializer = RegisterOrganizationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user, tokens, tenant = AuthService.register_organization_owner(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
            password_confirm=serializer.validated_data["password_confirm"],
            first_name=serializer.validated_data.get("first_name", ""),
            last_name=serializer.validated_data.get("last_name", ""),
            phone=serializer.validated_data.get("phone"),
            organization_name=serializer.validated_data["organization_name"],
            organization_type=serializer.validated_data["organization_type"],
            country=serializer.validated_data.get("country", "Angola"),
            city=serializer.validated_data.get("city", ""),
        )

        return created_response(
            data={
                "access": tokens["access"],
                "refresh": tokens["refresh"],
                "user": UserSerializer(user).data,
                "organization": OrganizationSerializer(tenant).data,
            },
            message="Organization owner registered successfully.",
        )


class LoginView(APIView):
    """Authenticate a user with email and password. Returns JWT tokens."""

    permission_classes = [AllowAny]

    @extend_schema(
        tags=["auth"],
        request=LoginSerializer,
        responses={200: TokenResponseSerializer},
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user, tokens = AuthService.login(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )

        return success_response(
            data={
                "access": tokens["access"],
                "refresh": tokens["refresh"],
                "user": UserSerializer(user).data,
            },
            message="Login successful.",
        )


class LogoutView(APIView):
    """Blacklist the provided refresh token to logout the user."""

    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["auth"], request=LogoutSerializer)
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        AuthService.logout(refresh_token=serializer.validated_data["refresh"])

        return success_response(message="Logout successful.")


class ForgotPasswordView(APIView):
    """
    Request a password reset email.

    Always returns 200 regardless of whether the email exists,
    to prevent user enumeration attacks.
    """

    permission_classes = [AllowAny]

    @extend_schema(tags=["auth"], request=ForgotPasswordSerializer)
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Silently handles unknown emails — no enumeration
        AuthService.request_password_reset(
            email=serializer.validated_data["email"]
        )

        return success_response(
            message="If an account with that email exists, a reset link has been sent."
        )


class ResetPasswordView(APIView):
    """
    Confirm a password reset using the token received by email.
    """

    permission_classes = [AllowAny]

    @extend_schema(tags=["auth"], request=ResetPasswordSerializer)
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        AuthService.confirm_password_reset(
            token=str(serializer.validated_data["token"]),
            new_password=serializer.validated_data["new_password"],
            new_password_confirm=serializer.validated_data["new_password_confirm"],
        )

        return success_response(
            message="Password reset successfully. You can now log in with your new password."
        )
