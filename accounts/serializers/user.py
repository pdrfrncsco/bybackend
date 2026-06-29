"""
BOLAYETU — User Serializers

Read serializers for User data representation.
These serializers are used for GET responses — never for mutations.
"""

from rest_framework import serializers

from accounts.models import User, TenantMembership


class UserSerializer(serializers.ModelSerializer):
    """
    Full user profile serializer.

    Used for: /api/v1/auth/me/ (GET response)
    """

    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "full_name",
            "phone",
            "status",
            "is_email_verified",
            "language",
            "timezone",
            "last_login",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class UserMinimalSerializer(serializers.ModelSerializer):
    """
    Minimal user representation for embedding in other resources.

    Used for: nested relationships (e.g. membership.user, comment.author)
    """

    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = ["id", "email", "full_name"]
        read_only_fields = fields


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating a user's profile via PATCH /api/v1/auth/me/.

    Only the fields below are updatable. Email and password
    changes have dedicated endpoints.
    """

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "phone",
            "language",
            "timezone",
        ]


class TenantMembershipSerializer(serializers.ModelSerializer):
    """Read-only serializer for tenant membership data."""

    tenant_name = serializers.CharField(source="tenant.name", read_only=True)
    tenant_slug = serializers.CharField(source="tenant.slug", read_only=True)

    class Meta:
        model = TenantMembership
        fields = [
            "id",
            "tenant",
            "tenant_name",
            "tenant_slug",
            "role",
            "is_active",
            "joined_at",
        ]
        read_only_fields = fields
