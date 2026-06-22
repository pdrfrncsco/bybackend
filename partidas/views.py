"""
BOLAYETU — Partidas View Layer
Skills: BOLAYETU_ARCHITECTURE, BOLAYETU_BACKEND_SKILL, BOLAYETU_MULTITENANT_SKILL

Rule: ViewSets ONLY orchestrate. Delegate queries to selectors and database writes to services.
"""

from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend

from .models import Match
from .serializers import MatchSerializer
from core.permissions import IsManager
from .selectors import MatchSelector
from .services import MatchService


class MatchViewSet(viewsets.ModelViewSet):
    permission_classes = [IsManager]
    serializer_class = MatchSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'round', 'tournament']
    search_fields = ['home_team__name', 'away_team__name']
    ordering_fields = ['date']

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Match.objects.none()
            
        tenant = getattr(self.request, 'tenant', None) or getattr(self.request.user, 'tenant', None)
        if not tenant:
            return Match.objects.none()

        selector = MatchSelector(tenant=tenant, user=self.request.user)
        team_id = self.request.query_params.get('team')
        
        return selector.list_matches(team_id=team_id)

    def perform_create(self, serializer):
        tenant = getattr(self.request, 'tenant', None) or getattr(self.request.user, 'tenant', None)
        if tenant:
            service = MatchService(user=self.request.user, tenant=tenant)
            
            # Identify which keys were explicitly sent in the request
            request_keys = set(self.request.data.keys()) if isinstance(self.request.data, dict) else None
            
            service.create_match(
                data=serializer.validated_data,
                request_keys=request_keys
            )

    def perform_update(self, serializer):
        tenant = getattr(self.request, 'tenant', None) or getattr(self.request.user, 'tenant', None)
        if tenant:
            service = MatchService(user=self.request.user, tenant=tenant)
            
            # Identify which keys were explicitly sent in the request
            request_keys = set(self.request.data.keys()) if isinstance(self.request.data, dict) else None
            
            service.update_match(
                match=serializer.instance,
                data=serializer.validated_data,
                request_keys=request_keys
            )

    def perform_destroy(self, instance):
        tenant = getattr(self.request, 'tenant', None) or getattr(self.request.user, 'tenant', None)
        if tenant:
            service = MatchService(user=self.request.user, tenant=tenant)
            service.delete_match(match=instance)
