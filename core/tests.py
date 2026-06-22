"""
Testes de validação das permissões da FASE 5.

Garante que as permissões de domínio (IsOrganizacao, IsClube, IsJogador, IsAdepto)
e as permissões legadas (IsAdmin, IsManager) funcionam corretamente com os
novos UserRole enums e continuam retrocompatíveis com os roles antigos.
"""
from django.test import RequestFactory, TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIRequestFactory
from accounts.models import UserRole
from core.permissions import (
    IsAdmin, IsManager, IsOrganizacao, IsClube, IsJogador, IsAdepto
)

User = get_user_model()


class PermissionsUnitTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def _make_user(self, role, username_suffix=''):
        return User.objects.create_user(
            username=f'testuser_{role}_{username_suffix}',
            email=f'test_{role}_{username_suffix}@example.com',
            password='password123',
            role=role
        )

    def _make_request(self, user):
        request = self.factory.get('/')
        request.user = user
        return request

    # ─── IsAdmin ─────────────────────────────────────────────────────────────

    def test_is_admin_allows_new_admin_role(self):
        user = self._make_user(UserRole.ADMIN, 'a')
        request = self._make_request(user)
        perm = IsAdmin()
        self.assertTrue(perm.has_permission(request, None))

    def test_is_admin_allows_superadmin_role(self):
        user = self._make_user(UserRole.SUPERADMIN, 'b')
        request = self._make_request(user)
        perm = IsAdmin()
        self.assertTrue(perm.has_permission(request, None))

    def test_is_admin_allows_legacy_admin_role(self):
        user = self._make_user(UserRole.LEGACY_ADMIN, 'c')
        request = self._make_request(user)
        perm = IsAdmin()
        self.assertTrue(perm.has_permission(request, None))

    def test_is_admin_denies_clube_role(self):
        user = self._make_user(UserRole.CLUBE, 'd')
        request = self._make_request(user)
        perm = IsAdmin()
        self.assertFalse(perm.has_permission(request, None))

    def test_is_admin_denies_adepto_role(self):
        user = self._make_user(UserRole.ADEPTO, 'e')
        request = self._make_request(user)
        perm = IsAdmin()
        self.assertFalse(perm.has_permission(request, None))

    # ─── IsManager ───────────────────────────────────────────────────────────

    def test_is_manager_allows_organizacao_role(self):
        user = self._make_user(UserRole.ORGANIZACAO, 'f')
        request = self._make_request(user)
        perm = IsManager()
        self.assertTrue(perm.has_permission(request, None))

    def test_is_manager_allows_legacy_manager(self):
        user = self._make_user(UserRole.LEGACY_MANAGER, 'g')
        request = self._make_request(user)
        perm = IsManager()
        self.assertTrue(perm.has_permission(request, None))

    def test_is_manager_denies_adepto(self):
        user = self._make_user(UserRole.ADEPTO, 'h')
        request = self._make_request(user)
        perm = IsManager()
        self.assertFalse(perm.has_permission(request, None))

    # ─── Domain Permissions ───────────────────────────────────────────────────

    def test_is_organizacao_allows_organizacao_role(self):
        user = self._make_user(UserRole.ORGANIZACAO, 'i')
        request = self._make_request(user)
        perm = IsOrganizacao()
        self.assertTrue(perm.has_permission(request, None))

    def test_is_organizacao_denies_clube_role(self):
        user = self._make_user(UserRole.CLUBE, 'j')
        request = self._make_request(user)
        perm = IsOrganizacao()
        self.assertFalse(perm.has_permission(request, None))

    def test_is_clube_allows_clube_role(self):
        user = self._make_user(UserRole.CLUBE, 'k')
        request = self._make_request(user)
        perm = IsClube()
        self.assertTrue(perm.has_permission(request, None))

    def test_is_clube_allows_organizacao_role(self):
        user = self._make_user(UserRole.ORGANIZACAO, 'l')
        request = self._make_request(user)
        perm = IsClube()
        self.assertTrue(perm.has_permission(request, None))

    def test_is_clube_denies_adepto_role(self):
        user = self._make_user(UserRole.ADEPTO, 'm')
        request = self._make_request(user)
        perm = IsClube()
        self.assertFalse(perm.has_permission(request, None))

    def test_is_jogador_allows_jogador_role(self):
        user = self._make_user(UserRole.JOGADOR, 'n')
        request = self._make_request(user)
        perm = IsJogador()
        self.assertTrue(perm.has_permission(request, None))

    def test_is_jogador_allows_clube_role(self):
        user = self._make_user(UserRole.CLUBE, 'o')
        request = self._make_request(user)
        perm = IsJogador()
        self.assertTrue(perm.has_permission(request, None))

    def test_is_jogador_denies_adepto_role(self):
        user = self._make_user(UserRole.ADEPTO, 'p')
        request = self._make_request(user)
        perm = IsJogador()
        self.assertFalse(perm.has_permission(request, None))

    def test_is_adepto_allows_any_authenticated_user(self):
        for role in [UserRole.ADEPTO, UserRole.JOGADOR, UserRole.CLUBE, UserRole.ORGANIZACAO, UserRole.ADMIN]:
            user = self._make_user(role, role)
            request = self._make_request(user)
            perm = IsAdepto()
            self.assertTrue(perm.has_permission(request, None), f"IsAdepto should allow role {role}")
