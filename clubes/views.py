"""
BOLAYETU — Clubes View Layer
Skills: BOLAYETU_ARCHITECTURE, BOLAYETU_BACKEND_SKILL, BOLAYETU_MULTITENANT_SKILL

Rule: ViewSets ONLY orchestrate. Delegate database reads to selectors and writes to services.
"""

from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import Club, Staff, ClubHistory
from .serializers import ClubSerializer, ClubListSerializer, ClubHistorySerializer, StaffSerializer
from .serializers_summary import ClubSummarySerializer
from core.permissions import IsManager, HasPermission
from .selectors import ClubSelector
from .services import ClubService


@extend_schema_view(
    list=extend_schema(
        tags=["Clubs"],
        description="Lista clubes do tenant atual. Requer utilizador autenticado."
    ),
    retrieve=extend_schema(
        tags=["Clubs"],
        description="Detalhes de clube do tenant atual. Requer utilizador autenticado."
    ),
    create=extend_schema(
        tags=["Clubs", "Admin/Manager Only"],
        description="Criar clube. Requer role MANAGER ou ADMIN ou permissões de gestão."
    ),
    partial_update=extend_schema(
        tags=["Clubs", "Admin/Manager Only"],
        description="Atualizar parcialmente clube. Requer role MANAGER ou ADMIN ou permissões de gestão."
    ),
    update=extend_schema(
        tags=["Clubs", "Admin/Manager Only"],
        description="Atualizar clube. Requer role MANAGER ou ADMIN ou permissões de gestão."
    ),
    destroy=extend_schema(
        tags=["Clubs", "Admin/Manager Only"],
        description="Remover clube. Requer role MANAGER ou ADMIN ou permissões de gestão."
    ),
)
class ClubViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'location', 'stadium_name']
    ordering_fields = ['name', 'founded_year', 'created_at']
    ordering = ['name']

    def get_permissions(self):
        if self.action in ["list", "retrieve", "summary_list", "summary_detail"]:
            return [permissions.AllowAny()]
        return [IsManager(), HasPermission()]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Club.objects.none()
            
        tenant = getattr(self.request, 'tenant', None) or getattr(self.request.user, 'tenant', None)
        selector = ClubSelector(tenant=tenant, user=self.request.user)
        
        # In details page, we want to prefetch relations
        if self.action in ['retrieve', 'update', 'partial_update']:
            if self.kwargs.get('pk'):
                try:
                    # Return a list matching the single detail to satisfy ViewSet queryset requirements
                    return Club.objects.filter(id=self.kwargs['pk']).prefetch_related('history', 'staff_members')
                except Exception:
                    pass
        
        return selector.list_clubs()

    def get_serializer_class(self):
        if self.action == 'list':
            return ClubListSerializer
        return ClubSerializer

    def perform_create(self, serializer):
        tenant = getattr(self.request, 'tenant', None) or getattr(self.request.user, 'tenant', None)
        service = ClubService(user=self.request.user, tenant=tenant)
        # Delegate object creation to the Service
        service.create_club(data=serializer.validated_data)

    def perform_update(self, serializer):
        tenant = getattr(self.request, 'tenant', None) or getattr(self.request.user, 'tenant', None)
        service = ClubService(user=self.request.user, tenant=tenant)
        # Delegate object update to the Service
        service.update_club(club=serializer.instance, data=serializer.validated_data)

    def perform_destroy(self, instance):
        tenant = getattr(self.request, 'tenant', None) or getattr(self.request.user, 'tenant', None)
        service = ClubService(user=self.request.user, tenant=tenant)
        service.delete_club(club=instance)

    @extend_schema(
        tags=["Clubs"],
        description="Lista resumida de clubes com sigla e nome curto.",
        responses=ClubSummarySerializer,
    )
    @action(detail=False, methods=["get"], url_path="summary")
    @method_decorator(cache_page(60))
    def summary_list(self, request):
        queryset = self.get_queryset()
        serializer = ClubSummarySerializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=["Clubs"],
        description="Detalhe resumido de um clube, focado em exibição compacta.",
        responses=ClubSummarySerializer,
    )
    @action(detail=True, methods=["get"], url_path="summary")
    @method_decorator(cache_page(60))
    def summary_detail(self, request, pk=None):
        obj = self.get_object()
        serializer = ClubSummarySerializer(obj)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        tags=["Club History", "Admin/Manager Only"],
        description="Lista histórico de clubes do tenant atual. Requer permissões de gestão (MANAGER/ADMIN)."
    ),
    retrieve=extend_schema(
        tags=["Club History", "Admin/Manager Only"],
        description="Detalhes de histórico de clube. Requer permissões de gestão (MANAGER/ADMIN)."
    ),
)
class ClubHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsManager, HasPermission]
    serializer_class = ClubHistorySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['club__name', 'season', 'tournament_name', 'placement']
    ordering_fields = ['season', 'tournament_name', 'created_at']
    ordering = ['-season']

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return ClubHistory.objects.none()
            
        tenant = getattr(self.request, 'tenant', None) or getattr(self.request.user, 'tenant', None)
        if not tenant:
            return ClubHistory.objects.none()
            
        selector = ClubSelector(tenant=tenant, user=self.request.user)
        return selector.list_club_history()


@extend_schema_view(
    list=extend_schema(
        tags=["Staff", "Admin/Manager Only"],
        description="Lista membros da equipa técnica do tenant atual. Requer permissões de gestão (MANAGER/ADMIN)."
    ),
    retrieve=extend_schema(
        tags=["Staff", "Admin/Manager Only"],
        description="Detalhes de membro da equipa técnica. Requer permissões de gestão (MANAGER/ADMIN)."
    ),
    create=extend_schema(
        tags=["Staff", "Admin/Manager Only"],
        description="Adicionar membro da equipa técnica. Requer permissões de gestão (MANAGER/ADMIN)."
    ),
    update=extend_schema(
        tags=["Staff", "Admin/Manager Only"],
        description="Atualizar membro da equipa técnica. Requer permissões de gestão (MANAGER/ADMIN)."
    ),
    partial_update=extend_schema(
        tags=["Staff", "Admin/Manager Only"],
        description="Atualizar parcialmente membro da equipa técnica. Requer permissões de gestão (MANAGER/ADMIN)."
    ),
    destroy=extend_schema(
        tags=["Staff", "Admin/Manager Only"],
        description="Remover membro da equipa técnica. Requer permissões de gestão (MANAGER/ADMIN)."
    ),
)
class StaffViewSet(viewsets.ModelViewSet):
    permission_classes = [IsManager, HasPermission]
    serializer_class = StaffSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'role', 'club__name']
    ordering_fields = ['name', 'role', 'created_at']
    ordering = ['name']
    filterset_fields = ['club']

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Staff.objects.none()
            
        tenant = getattr(self.request, 'tenant', None) or getattr(self.request.user, 'tenant', None)
        if not tenant:
            return Staff.objects.none()
            
        selector = ClubSelector(tenant=tenant, user=self.request.user)
        return selector.list_staff(club_id=self.request.query_params.get('club'))

    def perform_create(self, serializer):
        tenant = getattr(self.request, 'tenant', None) or getattr(self.request.user, 'tenant', None)
        service = ClubService(user=self.request.user, tenant=tenant)
        service.create_staff(data=serializer.validated_data)

    def perform_update(self, serializer):
        tenant = getattr(self.request, 'tenant', None) or getattr(self.request.user, 'tenant', None)
        service = ClubService(user=self.request.user, tenant=tenant)
        service.update_staff(staff=serializer.instance, data=serializer.validated_data)

    def perform_destroy(self, instance):
        tenant = getattr(self.request, 'tenant', None) or getattr(self.request.user, 'tenant', None)
        service = ClubService(user=self.request.user, tenant=tenant)
        service.delete_staff(staff=instance)
