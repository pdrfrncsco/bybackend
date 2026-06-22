"""
BOLAYETU — Classificacoes View Layer
Skills: BOLAYETU_ARCHITECTURE, BOLAYETU_BACKEND_SKILL, BOLAYETU_MULTITENANT_SKILL

Rule: ViewSets ONLY orchestrate. Delegate queries to selectors and database writes to services.
"""

from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import Standing
from .serializers import StandingSerializer
from core.permissions import IsManager
from .selectors import StandingSelector
from .services import StandingService


@extend_schema_view(
    list=extend_schema(
        tags=["Standings"],
        description="Tabela de classificação. Leitura pública; escrita requer role MANAGER ou ADMIN."
    ),
    retrieve=extend_schema(
        tags=["Standings"],
        description="Detalhes de classificação. Leitura pública; escrita requer role MANAGER ou ADMIN."
    ),
    create=extend_schema(
        tags=["Standings", "Admin/Manager Only"],
        description="Criar registos de classificação. Requer role MANAGER ou ADMIN."
    ),
    update=extend_schema(
        tags=["Standings", "Admin/Manager Only"],
        description="Atualizar classificação. Requer role MANAGER ou ADMIN."
    ),
    partial_update=extend_schema(
        tags=["Standings", "Admin/Manager Only"],
        description="Atualizar parcialmente classificação. Requer role MANAGER ou ADMIN."
    ),
    destroy=extend_schema(
        tags=["Standings", "Admin/Manager Only"],
        description="Remover registos de classificação. Requer role MANAGER ou ADMIN."
    ),
)
class StandingViewSet(viewsets.ModelViewSet):
    permission_classes = [IsManager]
    serializer_class = StandingSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['tournament', 'group', 'club']
    ordering_fields = ['points', 'goals_for', 'goals_against']
    ordering = ['-points', '-goals_for']

    def get_permissions(self):
        if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
            return [permissions.AllowAny()]
        return [IsManager()]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Standing.objects.none()

        tenant = getattr(self.request, 'tenant', None) or getattr(self.request.user, 'tenant', None)
        tournament_id = self.request.query_params.get('tournament')
        group_id = self.request.query_params.get('group')

        selector = StandingSelector(tenant=tenant, user=self.request.user)
        return selector.list_standings(tournament_id=tournament_id, group_id=group_id)

    def perform_create(self, serializer):
        tenant = getattr(self.request, 'tenant', None) or getattr(self.request.user, 'tenant', None)
        if tenant:
            serializer.save(tenant=tenant)

    @action(detail=False, methods=['post'])
    @extend_schema(
        tags=["Standings", "Admin/Manager Only"],
        description="Recalcula a classificação de um torneio. Requer role MANAGER ou ADMIN."
    )
    def recalculate(self, request):
        tenant = getattr(request, 'tenant', None) or getattr(request.user, 'tenant', None)
        if not tenant:
            return Response({'detail': 'Tenant não encontrado.'}, status=status.HTTP_400_BAD_REQUEST)

        tournament_id = request.data.get('tournament')
        if not tournament_id:
            return Response({'detail': 'ID do torneio é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)

        service = StandingService(user=request.user, tenant=tenant)
        service.recalculate_standings(tournament_id=tournament_id)

        # Retrieve and return general standings (group__isnull=True) for response
        selector = StandingSelector(tenant=tenant, user=request.user)
        queryset = selector.list_standings(tournament_id=tournament_id).filter(group__isnull=True)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
