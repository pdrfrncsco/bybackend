"""
BOLAYETU — Jogadores View Layer
Skills: BOLAYETU_ARCHITECTURE, BOLAYETU_BACKEND_SKILL, BOLAYETU_MULTITENANT_SKILL

Rule: ViewSets ONLY orchestrate. Delegate queries to selectors and database writes to services.
"""

from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import Player, PlayerHistory
from .serializers import PlayerSerializer, PlayerHistorySerializer
from .serializers_summary import PlayerSummarySerializer
from core.permissions import IsManager, HasPermission
from .selectors import PlayerSelector
from .services import PlayerService


class PlayerPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 100


@extend_schema_view(
    list=extend_schema(
        tags=["Players"],
        description="Lista jogadores. Disponível para utilizadores autenticados; escrita requer MANAGER ou ADMIN."
    ),
    retrieve=extend_schema(
        tags=["Players"],
        description="Detalhes de jogador. Disponível para utilizadores autenticados; escrita requer MANAGER ou ADMIN."
    ),
    create=extend_schema(
        tags=["Players"],
        description="Criar jogador. Requer role MANAGER ou ADMIN."
    ),
    partial_update=extend_schema(
        tags=["Players"],
        description="Atualizar parcialmente jogador. Requer role MANAGER ou ADMIN."
    ),
    update=extend_schema(
        tags=["Players"],
        description="Atualizar jogador. Requer role MANAGER ou ADMIN."
    ),
    destroy=extend_schema(
        tags=["Players"],
        description="Apagar jogador. Requer role MANAGER ou ADMIN."
    ),
)
class PlayerViewSet(viewsets.ModelViewSet):
    serializer_class = PlayerSerializer
    pagination_class = PlayerPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['club', 'position', 'nationality', 'status']
    search_fields = ['name', 'nickname']
    ordering_fields = ['name', 'number', 'age']

    def get_permissions(self):
        if self.action in ["list", "retrieve", "summary_list", "summary_detail"]:
            return [permissions.AllowAny()]
        return [IsManager(), HasPermission()]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Player.objects.none()
            
        tenant = getattr(self.request, 'tenant', None) or getattr(self.request.user, 'tenant', None)
        selector = PlayerSelector(tenant=tenant, user=self.request.user)
        
        club_id = self.request.query_params.get("club")
        search_query = self.request.query_params.get("search")
        
        return selector.list_players(club_id=club_id, search_query=search_query)

    @extend_schema(
        tags=["Players"],
        description="Lista resumida de jogadores, optimizada para listagens e dropdowns.",
        responses=PlayerSummarySerializer,
    )
    @action(detail=False, methods=["get"], url_path="summary")
    @method_decorator(cache_page(60))
    def summary_list(self, request):
        queryset = self.get_queryset()
        serializer = PlayerSummarySerializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=["Players"],
        description="Detalhe resumido de um jogador, focado em exibição compacta.",
        responses=PlayerSummarySerializer,
    )
    @action(detail=True, methods=["get"], url_path="summary")
    @method_decorator(cache_page(60))
    def summary_detail(self, request, pk=None):
        obj = self.get_object()
        serializer = PlayerSummarySerializer(obj)
        return Response(serializer.data)

    def perform_create(self, serializer):
        tenant = getattr(self.request, 'tenant', None) or getattr(self.request.user, 'tenant', None)
        service = PlayerService(user=self.request.user, tenant=tenant)
        service.create_player(data=serializer.validated_data)

    def perform_update(self, serializer):
        tenant = getattr(self.request, 'tenant', None) or getattr(self.request.user, 'tenant', None)
        service = PlayerService(user=self.request.user, tenant=tenant)
        service.update_player(player=serializer.instance, data=serializer.validated_data)

    def perform_destroy(self, instance):
        tenant = getattr(self.request, 'tenant', None) or getattr(self.request.user, 'tenant', None)
        service = PlayerService(user=self.request.user, tenant=tenant)
        service.delete_player(player=instance)


@extend_schema_view(
    list=extend_schema(
        tags=["Player History", "Admin/Manager Only"],
        description="Requer role MANAGER ou ADMIN."
    ),
    retrieve=extend_schema(
        tags=["Player History", "Admin/Manager Only"],
        description="Requer role MANAGER ou ADMIN."
    ),
    create=extend_schema(
        tags=["Player History", "Admin/Manager Only"],
        description="Requer role MANAGER ou ADMIN."
    ),
    partial_update=extend_schema(
        tags=["Player History", "Admin/Manager Only"],
        description="Requer role MANAGER ou ADMIN."
    ),
    update=extend_schema(
        tags=["Player History", "Admin/Manager Only"],
        description="Requer role MANAGER ou ADMIN."
    ),
    destroy=extend_schema(
        tags=["Player History", "Admin/Manager Only"],
        description="Requer role MANAGER ou ADMIN."
    ),
)
class PlayerHistoryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsManager, HasPermission]
    serializer_class = PlayerHistorySerializer
    pagination_class = PlayerPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['player', 'season', 'club']
    search_fields = ['player__name', 'season']
    ordering_fields = ['season']

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return PlayerHistory.objects.none()
            
        tenant = getattr(self.request, 'tenant', None) or getattr(self.request.user, 'tenant', None)
        if not tenant:
            return PlayerHistory.objects.none()
            
        selector = PlayerSelector(tenant=tenant, user=self.request.user)
        return selector.list_player_history()

    def perform_create(self, serializer):
        tenant = getattr(self.request, 'tenant', None) or getattr(self.request.user, 'tenant', None)
        service = PlayerService(user=self.request.user, tenant=tenant)
        service.create_player_history(data=serializer.validated_data)

    def perform_update(self, serializer):
        tenant = getattr(self.request, 'tenant', None) or getattr(self.request.user, 'tenant', None)
        service = PlayerService(user=self.request.user, tenant=tenant)
        service.update_player_history(history=serializer.instance, data=serializer.validated_data)

    def perform_destroy(self, instance):
        tenant = getattr(self.request, 'tenant', None) or getattr(self.request.user, 'tenant', None)
        service = PlayerService(user=self.request.user, tenant=tenant)
        service.delete_player_history(history=instance)
