"""
BOLAYETU — Accounts Admin Configuration
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from accounts.models import PasswordResetToken, TenantMembership, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ["email", "username", "full_name", "status", "is_email_verified", "is_staff"]
    list_filter = ["status", "is_email_verified", "is_staff", "is_superuser"]
    search_fields = ["email", "username", "first_name", "last_name"]
    ordering = ["-created_at"]

    # email is USERNAME_FIELD, so we modify fieldsets accordingly
    fieldsets = UserAdmin.fieldsets + (
        ("Profile Details", {"fields": ("phone", "status", "is_email_verified")}),
        ("User Preferences", {"fields": ("language", "timezone")}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Profile Details", {"fields": ("email", "first_name", "last_name", "phone")}),
    )


@admin.register(TenantMembership)
class TenantMembershipAdmin(admin.ModelAdmin):
    list_display = ["user", "tenant", "role", "is_active", "joined_at"]
    list_filter = ["role", "is_active", "tenant"]
    search_fields = ["user__email", "user__first_name", "user__last_name", "tenant__name"]
    ordering = ["-joined_at"]


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ["user", "token", "is_used", "expires_at", "created_at"]
    list_filter = ["is_used", "created_at", "expires_at"]
    search_fields = ["user__email", "token"]
    ordering = ["-created_at"]
    raw_id_fields = ["user"]
    readonly_fields = ["id", "token", "created_at", "updated_at"]
