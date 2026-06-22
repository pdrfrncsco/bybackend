from rest_framework import permissions
from accounts.models import UserRole


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permissão que permite apenas ao proprietário do perfil (ou administradores) editá-lo.
    """
    def has_object_permission(self, request, view, obj):
        # Permitir leitura para qualquer utilizador autenticado
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated

        # Permitir escrita apenas ao próprio utilizador (dono) ou administradores
        if not request.user or not request.user.is_authenticated:
            return False

        is_admin = request.user.role in [
            UserRole.ADMIN,
            UserRole.SUPERADMIN,
            UserRole.LEGACY_ADMIN,
        ] or request.user.is_superuser

        return obj.user == request.user or is_admin


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permissão que permite escrita apenas para administradores, leitura para utilizadores autenticados.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated

        if not request.user or not request.user.is_authenticated:
            return False

        return request.user.role in [
            UserRole.ADMIN,
            UserRole.SUPERADMIN,
            UserRole.LEGACY_ADMIN,
        ] or request.user.is_superuser
