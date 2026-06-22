"""
BOLAYETU — Torneios View Layer
Skills: BOLAYETU_ARCHITECTURE, BOLAYETU_BACKEND_SKILL, BOLAYETU_MULTITENANT_SKILL

Rule: ViewSets ONLY orchestrate. Delegate queries to selectors and database writes to services.
"""

from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import Tournament, TournamentGroup
from .serializers import TournamentSerializer, TournamentDetailSerializer, TournamentGroupSerializer
from core.permissions import IsManager
from .selectors import TournamentSelector
from .services import TournamentService


class PublicTournamentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for public access to active/upcoming/completed tournaments.
    """
    serializer_class = TournamentSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'tenant__name']
    filterset_fields = ['status', 'type', 'season']
    ordering_fields = ['start_date', 'name']

    def get_queryset(self):
        tenant_slug = self.request.query_params.get('tenant_slug') or self.request.query_params.get('org')
        selector = TournamentSelector()
        return selector.list_public_tournaments(
            tenant_slug=tenant_slug,
            status_list=['active', 'upcoming', 'completed']
        )

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TournamentDetailSerializer
        return TournamentSerializer


@extend_schema_view(
    list=extend_schema(
        tags=["Tournaments", "Admin/Manager Only"],
        description="Lista torneios do tenant atual. Requer role MANAGER ou ADMIN."
    ),
    retrieve=extend_schema(
        tags=["Tournaments", "Admin/Manager Only"],
        description="Detalhes de torneio do tenant atual. Requer role MANAGER ou ADMIN."
    ),
    create=extend_schema(
        tags=["Tournaments", "Admin/Manager Only"],
        description="Criar torneio para o tenant atual. Requer role MANAGER ou ADMIN."
    ),
    update=extend_schema(
        tags=["Tournaments", "Admin/Manager Only"],
        description="Atualizar torneio. Requer role MANAGER ou ADMIN."
    ),
    partial_update=extend_schema(
        tags=["Tournaments", "Admin/Manager Only"],
        description="Atualizar parcialmente torneio. Requer role MANAGER ou ADMIN."
    ),
    destroy=extend_schema(
        tags=["Tournaments", "Admin/Manager Only"],
        description="Remover torneio. Requer role MANAGER ou ADMIN."
    ),
)
class TournamentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsManager]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'season', 'type']
    search_fields = ['name']
    ordering_fields = ['start_date', 'created_at']

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Tournament.objects.none()
            
        tenant = getattr(self.request, 'tenant', None) or getattr(self.request.user, 'tenant', None)
        if not tenant:
            return Tournament.objects.none()
            
        selector = TournamentSelector(tenant=tenant, user=self.request.user)
        return selector.list_tournaments()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TournamentDetailSerializer
        return TournamentSerializer

    def perform_create(self, serializer):
        tenant = getattr(self.request, 'tenant', None) or getattr(self.request.user, 'tenant', None)
        service = TournamentService(user=self.request.user, tenant=tenant)
        service.create_tournament(data=serializer.validated_data)

    def perform_update(self, serializer):
        tenant = getattr(self.request, 'tenant', None) or getattr(self.request.user, 'tenant', None)
        service = TournamentService(user=self.request.user, tenant=tenant)
        service.update_tournament(tournament=serializer.instance, data=serializer.validated_data)

    def perform_destroy(self, instance):
        tenant = getattr(self.request, 'tenant', None) or getattr(self.request.user, 'tenant', None)
        service = TournamentService(user=self.request.user, tenant=tenant)
        service.delete_tournament(tournament=instance)

    @action(detail=True, methods=['post'])
    def generate_schedule(self, request, pk=None):
        tournament = self.get_object()
        
        start_date_str = request.data.get('start_date')
        interval_days = int(request.data.get('interval_days', 7))

        tenant = getattr(request, 'tenant', None) or getattr(request.user, 'tenant', None)
        service = TournamentService(user=request.user, tenant=tenant)
        
        matches_created = service.generate_tournament_schedule(
            tournament=tournament,
            start_date_str=start_date_str,
            interval_days=interval_days
        )
        
        return Response({
            'status': 'schedule generated',
            'matches_created': len(matches_created)
        })

    @action(detail=True, methods=['post'])
    def add_clubs(self, request, pk=None):
        tournament = self.get_object()
        club_ids = request.data.get('club_ids', [])
        
        if not club_ids:
             return Response({'detail': 'No clubs provided'}, status=status.HTTP_400_BAD_REQUEST)

        tenant = getattr(request, 'tenant', None) or getattr(request.user, 'tenant', None)
        service = TournamentService(user=request.user, tenant=tenant)
        count = service.add_clubs_to_tournament(tournament=tournament, club_ids=club_ids)
        
        return Response({'status': 'clubs added', 'count': count})

    @action(detail=True, methods=['post'])
    def remove_clubs(self, request, pk=None):
        tournament = self.get_object()
        club_ids = request.data.get('club_ids', [])
        
        if not club_ids:
             return Response({'detail': 'No clubs provided'}, status=status.HTTP_400_BAD_REQUEST)

        tenant = getattr(request, 'tenant', None) or getattr(request.user, 'tenant', None)
        service = TournamentService(user=request.user, tenant=tenant)
        count = service.remove_clubs_from_tournament(tournament=tournament, club_ids=club_ids)
        
        return Response({'status': 'clubs removed', 'count': count})

    @action(detail=True, methods=['post'])
    def set_champions(self, request, pk=None):
        tournament = self.get_object()
        champion_id = request.data.get('champion_club')
        runner_up_id = request.data.get('runner_up_club')

        tenant = getattr(request, 'tenant', None) or getattr(request.user, 'tenant', None)
        service = TournamentService(user=request.user, tenant=tenant)
        
        updated_tournament = service.set_tournament_champions(
            tournament=tournament,
            champion_id=champion_id,
            runner_up_id=runner_up_id
        )

        serializer = self.get_serializer(updated_tournament)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def set_groups(self, request, pk=None):
        tournament = self.get_object()
        groups_data = request.data.get('groups', [])

        tenant = getattr(request, 'tenant', None) or getattr(request.user, 'tenant', None)
        service = TournamentService(user=request.user, tenant=tenant)
        service.set_tournament_groups(tournament=tournament, groups_data=groups_data)
        
        return Response({'status': 'groups updated'})


class TournamentGroupViewSet(viewsets.ModelViewSet):
    permission_classes = [IsManager]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tournament']
    search_fields = ['name']
    ordering_fields = ['name']

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return TournamentGroup.objects.none()
            
        tenant = getattr(self.request, 'tenant', None) or getattr(self.request.user, 'tenant', None)
        if not tenant:
            return TournamentGroup.objects.none()
            
        selector = TournamentSelector(tenant=tenant, user=self.request.user)
        tournament_id = self.request.query_params.get('tournament')
        return selector.list_tournament_groups(tournament_id=tournament_id)

    def get_serializer_class(self):
        return TournamentGroupSerializer

    def perform_create(self, serializer):
        tenant = getattr(self.request, 'tenant', None) or getattr(self.request.user, 'tenant', None)
        # Note: TournamentGroup is small enough that we can just pass validated data to create.
        # Or save directly if we choose. But let's build it via a Service if standard, or let serializer do it
        # as it is a straightforward model. Let's let the serializer save it with tenant parameter.
        serializer.save(tenant=tenant)
