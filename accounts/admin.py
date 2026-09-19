"""
BOLAYETU — Accounts Admin Configuration
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html, mark_safe

from accounts.models import PasswordResetToken, TenantMembership, User
from clubs.models import ClubMember
from players.models import Player


class TenantMembershipInline(admin.TabularInline):
    model = TenantMembership
    fk_name = "user"
    extra = 0
    autocomplete_fields = ["tenant"]
    fields = ["tenant", "role", "is_active", "joined_at"]
    readonly_fields = ["joined_at"]
    ordering = ["-joined_at"]
    show_change_link = True
    verbose_name = "Membro da Organização / Tenant"
    verbose_name_plural = "Membros da Organização / Tenant"


class UserClubMemberInline(admin.TabularInline):
    model = ClubMember
    extra = 0
    autocomplete_fields = ["club"]
    fields = ["club", "role", "jersey_number", "position", "is_active", "joined_at"]
    ordering = ["-is_active", "club__name"]
    show_change_link = True
    verbose_name = "Função / Membro de Clube"
    verbose_name_plural = "Funções / Membros de Clubes"


class PlayerProfileInline(admin.StackedInline):
    model = Player
    extra = 0
    max_num = 1
    fk_name = "user"
    fields = [
        "first_name",
        "last_name",
        "primary_position",
        "shirt_number",
        "nationality",
        "status",
        "is_public",
    ]
    show_change_link = True
    verbose_name = "Perfil de Atleta / Jogador Vinculado"
    verbose_name_plural = "Perfil de Atleta / Jogador Vinculado"


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = [
        "email",
        "username",
        "full_name",
        "status",
        "tenants_display",
        "clubs_display",
        "player_display",
        "is_staff",
    ]
    list_filter = ["status", "is_email_verified", "is_staff", "is_superuser"]
    search_fields = ["email", "username", "first_name", "last_name"]
    ordering = ["-created_at"]
    inlines = [TenantMembershipInline, UserClubMemberInline, PlayerProfileInline]

    # email is USERNAME_FIELD, so we modify fieldsets accordingly
    fieldsets = UserAdmin.fieldsets + (
        ("Profile Details", {"fields": ("phone", "status", "is_email_verified")}),
        ("User Preferences", {"fields": ("language", "timezone")}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Profile Details", {"fields": ("email", "first_name", "last_name", "phone")}),
    )

    def tenants_display(self, obj):
        memberships = list(obj.memberships.select_related("tenant").filter(is_active=True)[:3])
        if not memberships:
            return "—"
        names = [f"{m.tenant.name} ({m.get_role_display()})" for m in memberships]
        return ", ".join(names)
    tenants_display.short_description = "Organizações"

    def clubs_display(self, obj):
        memberships = list(obj.club_memberships.select_related("club").filter(is_active=True)[:3])
        if not memberships:
            return "—"
        names = [f"{m.club.name} ({m.role_label})" for m in memberships]
        return ", ".join(names)
    clubs_display.short_description = "Clubes"

    def player_display(self, obj):
        try:
            p = getattr(obj, "player_profile", None)
            if p:
                return format_html(
                    '<a href="/admin/players/player/{}/change/">⚽ {} ({})</a>',
                    p.pk,
                    p.full_name,
                    p.get_primary_position_display(),
                )
        except Exception:
            pass
        return mark_safe('<span style="color:gray;">—</span>')
    player_display.short_description = "Perfil Atleta"


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
