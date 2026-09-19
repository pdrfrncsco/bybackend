"""
BOLAYETU — PlayerCategory Views

API endpoints for managing player categories at organization and club levels.
"""

import uuid
from django.db.models import Q
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from accounts.permissions import IsActiveAccount
from common.responses import created_response, error_response, success_response
from core.models import Tenant
from clubs.models import Club
from players.models.category import PlayerCategory
from players.serializers.category_serializers import (
    PlayerCategorySerializer,
    PlayerCategoryCreateSerializer,
    PlayerCategoryUpdateSerializer,
)


def _resolve_tenant(request, org_id_or_slug: str = None):
    if org_id_or_slug in (None, "", "me"):
        if request and hasattr(request, "user") and request.user and request.user.is_authenticated:
            try:
                from organizations.services import OrganizationService
                tenant = OrganizationService.get_organization_for_user(user=request.user)
                if tenant:
                    return tenant
            except Exception:
                pass
            membership = request.user.tenant_memberships.filter(is_active=True).select_related("tenant").first()
            if membership:
                return membership.tenant

        if request and getattr(request, "tenant", None):
            return request.tenant

        return Tenant.objects.filter(status=Tenant.TenantStatus.ACTIVE).first() or Tenant.objects.first()

    try:
        uuid.UUID(str(org_id_or_slug))
        tenant = Tenant.objects.filter(id=org_id_or_slug).first()
    except (ValueError, TypeError):
        tenant = Tenant.objects.filter(slug=org_id_or_slug).first()

    if not tenant:
        if request and getattr(request, "tenant", None):
            return request.tenant
        return Tenant.objects.filter(status=Tenant.TenantStatus.ACTIVE).first() or Tenant.objects.first()

    return tenant


def _resolve_club(request, club_id_or_slug: str = None):
    if club_id_or_slug in (None, "", "me"):
        if request and hasattr(request, "user") and request.user and request.user.is_authenticated:
            try:
                from clubs.services import ClubService
                club = ClubService.get_club_for_user(user=request.user)
                if club:
                    return club
            except Exception:
                pass
            club_member = request.user.club_memberships.filter(is_active=True).select_related("club", "club__tenant").first()
            if club_member:
                return club_member.club
        return None

    try:
        uuid.UUID(str(club_id_or_slug))
        club = Club.objects.select_related("tenant").filter(id=club_id_or_slug).first()
    except (ValueError, TypeError):
        club = Club.objects.select_related("tenant").filter(slug=club_id_or_slug).first()
    return club


class OrganizationCategoriesView(APIView):
    """
    List or create official player categories for an organization / federation.
    """

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated(), IsActiveAccount()]

    @extend_schema(tags=["categories"], responses={200: PlayerCategorySerializer(many=True)})
    def get(self, request, org_id: str = None, slug: str = None, **kwargs):
        tenant = _resolve_tenant(request, org_id or slug or kwargs.get("org_id_or_slug"))
        if not tenant:
            return success_response(data=[], message="Nenhuma organização encontrada.")

        categories = (
            PlayerCategory.objects
            .filter(tenant=tenant, scope=PlayerCategory.Scope.FEDERATION)
            .order_by("display_order", "min_age", "name")
        )
        serializer = PlayerCategorySerializer(categories, many=True)
        return success_response(data=serializer.data, message="Categorias da federação recuperadas com sucesso.")

    @extend_schema(tags=["categories"], request=PlayerCategoryCreateSerializer, responses={201: PlayerCategorySerializer})
    def post(self, request, org_id: str = None, slug: str = None, **kwargs):
        tenant = _resolve_tenant(request, org_id or slug)
        if not tenant:
            return error_response(message="Organização não encontrada.", status_code=404)

        serializer = PlayerCategoryCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(message="Dados inválidos.", errors=serializer.errors, status_code=400)

        category = serializer.save(
            tenant=tenant,
            club=None,
            scope=PlayerCategory.Scope.FEDERATION,
            is_custom=False,
        )
        output_serializer = PlayerCategorySerializer(category)
        return created_response(data=output_serializer.data, message="Categoria oficial criada com sucesso.")


class ClubCategoriesView(APIView):
    """
    List all categories available to a club (federation + custom) or create a custom category.
    """

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated(), IsActiveAccount()]

    @extend_schema(tags=["categories"], responses={200: PlayerCategorySerializer(many=True)})
    def get(self, request, club_id: str = None, slug: str = None, **kwargs):
        club = _resolve_club(request, club_id or slug)
        if not club:
            return error_response(message="Clube não encontrado.", status_code=404)

        # Retrieve both official federation categories and club custom categories
        categories = (
            PlayerCategory.objects
            .filter(
                Q(tenant=club.tenant, scope=PlayerCategory.Scope.FEDERATION) |
                Q(club=club, scope=PlayerCategory.Scope.CLUB)
            )
            .order_by("display_order", "min_age", "name")
        )
        serializer = PlayerCategorySerializer(categories, many=True)
        return success_response(data=serializer.data, message="Categorias do clube recuperadas com sucesso.")

    @extend_schema(tags=["categories"], request=PlayerCategoryCreateSerializer, responses={201: PlayerCategorySerializer})
    def post(self, request, club_id: str = None, slug: str = None, **kwargs):
        club = _resolve_club(request, club_id or slug)
        if not club:
            return error_response(message="Clube não encontrado.", status_code=404)

        serializer = PlayerCategoryCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(message="Dados inválidos.", errors=serializer.errors, status_code=400)

        category = serializer.save(
            tenant=club.tenant,
            club=club,
            scope=PlayerCategory.Scope.CLUB,
            is_custom=True,
        )
        output_serializer = PlayerCategorySerializer(category)
        return created_response(data=output_serializer.data, message="Categoria personalizada criada com sucesso.")


class ClubCategoryDetailView(APIView):
    """
    Update or delete a custom player category for a club.
    """

    permission_classes = [IsAuthenticated, IsActiveAccount]

    @extend_schema(tags=["categories"], request=PlayerCategoryUpdateSerializer, responses={200: PlayerCategorySerializer})
    def patch(self, request, club_id: str = None, slug: str = None, category_id: str = None, **kwargs):
        club = _resolve_club(request, club_id or slug)
        if not club:
            return error_response(message="Clube não encontrado.", status_code=404)

        category = PlayerCategory.objects.filter(id=category_id, club=club).first()
        if not category:
            return error_response(message="Categoria personalizada não encontrada.", status_code=404)

        serializer = PlayerCategoryUpdateSerializer(category, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response(message="Dados inválidos.", errors=serializer.errors, status_code=400)

        serializer.save()
        output_serializer = PlayerCategorySerializer(category)
        return success_response(data=output_serializer.data, message="Categoria atualizada com sucesso.")

    @extend_schema(tags=["categories"], responses={200: None})
    def delete(self, request, club_id: str = None, slug: str = None, category_id: str = None, **kwargs):
        club = _resolve_club(request, club_id or slug)
        if not club:
            return error_response(message="Clube não encontrado.", status_code=404)

        category = PlayerCategory.objects.filter(id=category_id, club=club).first()
        if not category:
            return error_response(message="Categoria personalizada não encontrada.", status_code=404)

        # Check if players are enrolled
        active_count = category.registrations.filter(status__in=["registered", "loaned"]).count()
        if active_count > 0:
            return error_response(
                message=f"Não é possível eliminar uma categoria com {active_count} atletas inscritos.",
                status_code=400,
            )

        category.delete()
        return success_response(data=None, message="Categoria eliminada com sucesso.")
