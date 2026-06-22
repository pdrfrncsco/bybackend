from rest_framework import permissions
from accounts.models import UserRole


class CanManageClubeOrganizacaoRequest(permissions.BasePermission):
    """
    Permite criação apenas para Clubes.
    Permite atualização/decisão apenas para a Organização destino ou Administradores.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
            
        if view.action == 'create':
            # Apenas clubes podem solicitar afiliação
            return request.user.role in [
                UserRole.CLUBE,
                UserRole.ADMIN,
                UserRole.SUPERADMIN,
                UserRole.LEGACY_ADMIN
            ] or request.user.is_superuser
            
        return True

    def has_object_permission(self, request, view, obj):
        # Apenas dono do clube solicitante, dono da organização destino ou admin podem ver/decidir
        is_admin = request.user.role in [
            UserRole.ADMIN,
            UserRole.SUPERADMIN,
            UserRole.LEGACY_ADMIN
        ] or request.user.is_superuser

        is_club_owner = obj.clube.user == request.user
        is_org_owner = obj.organizacao.user == request.user

        if request.method in permissions.SAFE_METHODS:
            return is_club_owner or is_org_owner or is_admin

        # Apenas dono da organização ou admin podem alterar/decidir
        return is_org_owner or is_admin


class CanManageJogadorClubeRequest(permissions.BasePermission):
    """
    Permite criação apenas para Jogadores.
    Permite atualização/decisão apenas para o Clube destino ou Administradores.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
            
        if view.action == 'create':
            # Apenas jogadores podem solicitar ingresso
            return request.user.role in [
                UserRole.JOGADOR,
                UserRole.ADMIN,
                UserRole.SUPERADMIN,
                UserRole.LEGACY_ADMIN
            ] or request.user.is_superuser
            
        return True

    def has_object_permission(self, request, view, obj):
        is_admin = request.user.role in [
            UserRole.ADMIN,
            UserRole.SUPERADMIN,
            UserRole.LEGACY_ADMIN
        ] or request.user.is_superuser

        is_player_owner = obj.jogador.user == request.user
        is_club_owner = obj.clube.user == request.user

        if request.method in permissions.SAFE_METHODS:
            return is_player_owner or is_club_owner or is_admin

        # Apenas dono do clube ou admin podem decidir
        return is_club_owner or is_admin
