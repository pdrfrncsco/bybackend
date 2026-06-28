"""
BOLAYETU — Accounts User Views
User Profile and Membership Management
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from accounts.services.user_service import UserService
from accounts.selectors import UserSelector
from accounts.serializers.user import (
    UserSerializer,
    UserUpdateSerializer,
    TenantMembershipSerializer,
)
from accounts.serializers.auth import ChangePasswordSerializer
from accounts.permissions import IsActiveAccount, IsAccountOwner
from common.responses import success_response


class MeView(APIView):
    """
    Retrieve or update the authenticated user's profile.
    """
    permission_classes = [IsAuthenticated, IsActiveAccount]

    @extend_schema(
        tags=["users"],
        responses={200: UserSerializer},
    )
    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return success_response(
            data=serializer.data,
            message="User profile retrieved successfully."
        )

    @extend_schema(
        tags=["users"],
        request=UserUpdateSerializer,
        responses={200: UserSerializer},
    )
    def patch(self, request):
        serializer = UserUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        user = UserService.update_profile(
            user=request.user,
            first_name=serializer.validated_data.get("first_name"),
            last_name=serializer.validated_data.get("last_name"),
            phone=serializer.validated_data.get("phone"),
            language=serializer.validated_data.get("language"),
            timezone=serializer.validated_data.get("timezone"),
        )

        return success_response(
            data=UserSerializer(user).data,
            message="User profile updated successfully."
        )


class ChangePasswordView(APIView):
    """
    Change password for the authenticated user.
    """
    permission_classes = [IsAuthenticated, IsActiveAccount]
    serializer_class = ChangePasswordSerializer

    @extend_schema(
        tags=["users"],
        request=ChangePasswordSerializer,
        responses={200: None},
    )
    def post(self, request):
        serializer = self.serializer_class(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        UserService.change_password(
            user=request.user,
            old_password=serializer.validated_data["old_password"],
            new_password=serializer.validated_data["new_password"],
            new_password_confirm=serializer.validated_data["new_password_confirm"],
        )

        return success_response(message="Password changed successfully.")


class UserMembershipsView(APIView):
    """
    Retrieve all tenant memberships for the authenticated user.
    """
    permission_classes = [IsAuthenticated, IsActiveAccount]

    @extend_schema(
        tags=["users"],
        responses={200: TenantMembershipSerializer(many=True)},
    )
    def get(self, request):
        memberships = UserSelector.get_memberships_for_user(user=request.user)
        serializer = TenantMembershipSerializer(memberships, many=True)
        return success_response(
            data=serializer.data,
            message="User memberships retrieved successfully."
        )
