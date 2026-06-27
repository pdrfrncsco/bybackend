from rest_framework import permissions
from accounts.models import UserRole


class HasPermission(permissions.BasePermission):
    required_permissions = []

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        codes = getattr(view, "required_permissions", None) or self.required_permissions
        if not codes:
            return True
        tenant = getattr(user, "tenant", None)
        for code in codes:
            if user.has_permission(code, tenant=tenant):
                return True
        return False


class IsAdmin(permissions.BasePermission):
    """Permite acesso a administradores da plataforma e tenants."""
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.role in [
            UserRole.ADMIN,
            UserRole.SUPERADMIN,
            UserRole.LEGACY_ADMIN,
        ] or user.is_superuser:
            return True
        tenant = getattr(user, "tenant", None)
        if user.has_permission("manage_tenant_settings", tenant=tenant):
            return True
        if user.has_permission("manage_platform", tenant=None):
            return True
        return False


class IsManager(permissions.BasePermission):
    """Permite acesso a gestores, administradores e organizações."""
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.role in [
            UserRole.ADMIN,
            UserRole.SUPERADMIN,
            UserRole.LEGACY_ADMIN,
            UserRole.LEGACY_MANAGER,
            UserRole.ADS_MANAGER,
            UserRole.ORGANIZACAO,
        ] or user.is_superuser:
            return True
        tenant = getattr(user, "tenant", None)
        if user.has_permission("manage_team", tenant=tenant):
            return True
        if user.has_permission("manage_players", tenant=tenant):
            return True
        if user.has_permission("manage_ads", tenant=tenant):
            return True
        return False


# ─── Permissões de Domínio Desportivo ────────────────────────────────────────

class IsOrganizacao(permissions.BasePermission):
    """
    Permite acesso apenas a utilizadores com perfil de Organização.
    Administradores também são aceites.
    """
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user.role in [
            UserRole.ORGANIZACAO,
            UserRole.ADMIN,
            UserRole.SUPERADMIN,
            UserRole.LEGACY_ADMIN,
        ] or user.is_superuser


class IsClube(permissions.BasePermission):
    """
    Permite acesso apenas a utilizadores com perfil de Clube.
    Organizações e Administradores também são aceites.
    """
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user.role in [
            UserRole.CLUBE,
            UserRole.ORGANIZACAO,
            UserRole.ADMIN,
            UserRole.SUPERADMIN,
            UserRole.LEGACY_ADMIN,
        ] or user.is_superuser


class IsJogador(permissions.BasePermission):
    """
    Permite acesso apenas a utilizadores com perfil de Jogador.
    Clubs e Administradores também são aceites.
    """
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user.role in [
            UserRole.JOGADOR,
            UserRole.CLUBE,
            UserRole.ADMIN,
            UserRole.SUPERADMIN,
            UserRole.LEGACY_ADMIN,
        ] or user.is_superuser


class IsAdepto(permissions.BasePermission):
    """
    Permite acesso a adeptos autenticados. Qualquer utilizador autenticado pode consumir.
    """
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return True


class IsViewer(permissions.BasePermission):
    """Permite acesso a qualquer utilizador autenticado (modo leitura)."""
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return True


class IsTenantMember(permissions.BasePermission):
    """Garante que o utilizador pertence ao mesmo tenant do objeto."""
    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.role in [
            UserRole.ADMIN,
            UserRole.SUPERADMIN,
            UserRole.LEGACY_ADMIN,
        ] or user.is_superuser:
            return True
        if not hasattr(user, "tenant") or not hasattr(obj, "tenant"):
            return False
        return user.tenant == obj.tenant


class IsAuthenticatedAndSubscribed(permissions.BasePermission):
    """Permite acesso a utilizadores autenticados com subscrição activa."""
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return True
