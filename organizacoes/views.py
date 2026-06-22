"""
BOLAYETU — Organizations View Layer
Skills: BOLAYETU_ARCHITECTURE, BOLAYETU_BACKEND_SKILL, BOLAYETU_MULTITENANT_SKILL

Rule: ViewSets ONLY orchestrate. No business rules or direct DB reads here.
"""

from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from clubes.serializers import ClubListSerializer
from torneios.serializers import TournamentSerializer
from .serializers import (
    OrganizationSerializer,
    PublicOrganizationSerializer,
    OrganizationHistoryEntrySerializer,
)
from .selectors import OrganizationSelector
from .services import OrganizationService


class OrganizationViewSet(viewsets.GenericViewSet):
    """
    ViewSet for handling Organization (Tenant) operations.
    Acts purely as an orchestrator between selectors, services, and serializers.
    """
    serializer_class = OrganizationSerializer

    def get_permissions(self):
        # Public actions allowed for anyone
        public_actions = [
            'public_list',
            'public_detail',
            'public_tournaments',
            'public_clubs',
            'public_history',
            'public_kpis',
        ]
        if self.action in public_actions:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    # ─── Auth User Scoped Actions ───────────────────────────────────

    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        tenant = getattr(request.user, 'tenant', None)
        if tenant is None:
            return Response({'detail': 'Tenant não definido.'}, status=400)
        serializer = self.get_serializer(tenant)
        return Response(serializer.data)

    @me.mapping.put
    def update_me(self, request):
        tenant = getattr(request.user, 'tenant', None)
        if tenant is None:
            return Response({'detail': 'Tenant não definido.'}, status=400)
        
        service = OrganizationService(user=request.user, tenant=tenant)
        updated_tenant = service.update_organization(tenant, data=request.data)
        
        serializer = self.get_serializer(updated_tenant)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='me/logo')
    def upload_logo(self, request):
        tenant = getattr(request.user, 'tenant', None)
        if tenant is None:
            return Response({'detail': 'Tenant não definido.'}, status=400)
        
        logo_file = request.FILES.get('logo') or request.data.get('logo')
        if not logo_file:
            return Response({'detail': 'Nenhum ficheiro enviado.'}, status=400)
            
        service = OrganizationService(user=request.user, tenant=tenant)
        updated_tenant = service.upload_logo(tenant, logo_file=logo_file)
        
        serializer = self.get_serializer(updated_tenant)
        return Response(serializer.data)

    # ─── Public Discovery Actions ───────────────────────────────────

    @action(detail=False, methods=['get'], url_path='public', serializer_class=PublicOrganizationSerializer)
    def public_list(self, request):
        search_query = request.query_params.get('search')
        org_type = request.query_params.get('type')
        
        selector = OrganizationSelector(user=request.user)
        tenants = selector.list_public_organizations(search_query=search_query, org_type=org_type)
        
        serializer = self.get_serializer(tenants, many=True)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['get'],
        url_path='public/(?P<slug>[^/.]+)',
        serializer_class=OrganizationSerializer,
    )
    def public_detail(self, request, slug=None):
        selector = OrganizationSelector(user=request.user)
        tenant = selector.get_public_detail(slug)
        serializer = self.get_serializer(tenant)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['post'],
        url_path='public/(?P<slug>[^/.]+)/subscribe',
    )
    def subscribe(self, request, slug=None):
        selector = OrganizationSelector(user=request.user)
        tenant = selector.get_public_detail(slug)
        
        service = OrganizationService(user=request.user)
        service.subscribe_user(tenant=tenant)
        
        return Response({'subscribed': True, 'organization_id': str(tenant.id)})

    @action(
        detail=False,
        methods=['post'],
        url_path='public/(?P<slug>[^/.]+)/unsubscribe',
    )
    def unsubscribe(self, request, slug=None):
        selector = OrganizationSelector(user=request.user)
        tenant = selector.get_public_detail(slug)
        
        service = OrganizationService(user=request.user)
        service.unsubscribe_user(tenant=tenant)
        
        return Response({'subscribed': False, 'organization_id': str(tenant.id)})

    @action(
        detail=False,
        methods=['get'],
        url_path='public/(?P<slug>[^/.]+)/tournaments',
        serializer_class=TournamentSerializer,
    )
    def public_tournaments(self, request, slug=None):
        selector = OrganizationSelector(user=request.user)
        tenant = selector.get_public_detail(slug)
        tournaments = selector.get_organization_tournaments(tenant)
        
        serializer = TournamentSerializer(tournaments, many=True)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['get'],
        url_path='public/(?P<slug>[^/.]+)/clubs',
        serializer_class=ClubListSerializer,
    )
    def public_clubs(self, request, slug=None):
        selector = OrganizationSelector(user=request.user)
        tenant = selector.get_public_detail(slug)
        clubs = selector.get_organization_clubs(tenant)
        
        serializer = ClubListSerializer(clubs, many=True)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['get'],
        url_path='public/(?P<slug>[^/.]+)/history',
        serializer_class=OrganizationHistoryEntrySerializer,
    )
    def public_history(self, request, slug=None):
        selector = OrganizationSelector(user=request.user)
        tenant = selector.get_public_detail(slug)
        history_data = selector.get_organization_history(tenant)
        
        serializer = self.get_serializer(history_data, many=True)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['get'],
        url_path='public/(?P<slug>[^/.]+)/kpis',
    )
    def public_kpis(self, request, slug=None):
        selector = OrganizationSelector(user=request.user)
        tenant = selector.get_public_detail(slug)
        kpi_data = selector.get_organization_kpis(tenant)
        
        return Response(kpi_data)
