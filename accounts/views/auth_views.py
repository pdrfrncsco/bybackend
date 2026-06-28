"""
BOLAYETU — Accounts Auth Views
Authentication and Token Management
"""

from rest_framework import serializers, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema

from accounts.services.auth_service import AuthService
from accounts.serializers.auth import (
    RegisterSerializer,
    LoginSerializer,
    LogoutSerializer,
    TokenResponseSerializer,
)
from accounts.serializers.user import UserSerializer
from common.responses import success_response, created_response, error_response



class RegisterView(APIView):
    """
    Register a new user account.
    Returns access and refresh JWT tokens upon successful registration.
    """
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    @extend_schema(
        tags=["auth"],
        request=RegisterSerializer,
        responses={201: TokenResponseSerializer},
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user, tokens = AuthService.register(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
            password_confirm=serializer.validated_data["password_confirm"],
            first_name=serializer.validated_data.get("first_name", ""),
            last_name=serializer.validated_data.get("last_name", ""),
            phone=serializer.validated_data.get("phone"),
        )

        response_data = {
            "access": tokens["access"],
            "refresh": tokens["refresh"],
            "user": UserSerializer(user).data,
        }

        return created_response(
            data=response_data,
            message="User registered successfully."
        )


class LoginView(APIView):
    """
    Authenticate a user with email and password.
    Returns access and refresh JWT tokens.
    """
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    @extend_schema(
        tags=["auth"],
        request=LoginSerializer,
        responses={200: TokenResponseSerializer},
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user, tokens = AuthService.login(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )

        response_data = {
            "access": tokens["access"],
            "refresh": tokens["refresh"],
            "user": UserSerializer(user).data,
        }

        return success_response(
            data=response_data,
            message="Login successful."
        )


class LogoutView(APIView):
    """
    Blacklist the provided refresh token to logout the user.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer

    @extend_schema(
        tags=["auth"],
        request=LogoutSerializer,
        responses={200: serializers.Serializer},  # Empty on success
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        AuthService.logout(refresh_token=serializer.validated_data["refresh"])

        return success_response(message="Logout successful.")
