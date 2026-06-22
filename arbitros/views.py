from django.db import transaction
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import ValidationError
from drf_spectacular.utils import extend_schema, extend_schema_view
from .models import Referee, RefereeAvailability
from .serializers import RefereeSerializer, RefereeAvailabilitySerializer
from core.permissions import IsManager, HasPermission

class RefereePagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 100


@extend_schema_view(
    list=extend_schema(
        tags=["Referees"],
        description="Lista árbitros. Disponível para utilizadores autenticados; escrita requer MANAGER ou ADMIN."
    ),
    retrieve=extend_schema(
        tags=["Referees"],
        description="Detalhes de árbitro. Disponível para utilizadores autenticados; escrita requer MANAGER ou ADMIN."
    ),
    create=extend_schema(
        tags=["Referees"],
        description="Criar árbitro. Requer role MANAGER ou ADMIN."
    ),
    partial_update=extend_schema(
        tags=["Referees"],
        description="Atualizar parcialmente árbitro. Requer role MANAGER ou ADMIN."
    ),
    update=extend_schema(
        tags=["Referees"],
        description="Atualizar árbitro. Requer role MANAGER ou ADMIN."
    ),
    destroy=extend_schema(
        tags=["Referees"],
        description="Apagar árbitro. Requer role MANAGER ou ADMIN."
    ),
)
class RefereeViewSet(viewsets.ModelViewSet):
    serializer_class = RefereeSerializer
    pagination_class = RefereePagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['name', 'bi', 'phone', 'email']
    ordering_fields = ['name', 'category', 'created_at']

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.IsAuthenticated()]
        return [IsManager(), HasPermission()]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Referee.objects.none()
        user = getattr(self.request, "user", None)
        tenant = getattr(user, "tenant", None)
        queryset = Referee.objects.all().order_by('name', 'id')
        if tenant:
            queryset = queryset.filter(tenant=tenant)
        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        tenant = getattr(user, "tenant", None)
        if not tenant:
            raise ValidationError({"detail": "Tenant não definido."})
        with transaction.atomic():
            serializer.save(tenant=tenant)


@extend_schema_view(
    list=extend_schema(
        tags=["Referee Availability", "Admin/Manager Only"],
        description="Lista disponibilidade de árbitros. Requer role MANAGER ou ADMIN."
    ),
    retrieve=extend_schema(
        tags=["Referee Availability", "Admin/Manager Only"],
        description="Detalhe de disponibilidade. Requer role MANAGER ou ADMIN."
    ),
    create=extend_schema(
        tags=["Referee Availability", "Admin/Manager Only"],
        description="Criar disponibilidade de árbitro. Requer role MANAGER ou ADMIN."
    ),
    partial_update=extend_schema(
        tags=["Referee Availability", "Admin/Manager Only"],
        description="Atualizar disponibilidade de árbitro. Requer role MANAGER ou ADMIN."
    ),
    update=extend_schema(
        tags=["Referee Availability", "Admin/Manager Only"],
        description="Atualizar disponibilidade de árbitro. Requer role MANAGER ou ADMIN."
    ),
    destroy=extend_schema(
        tags=["Referee Availability", "Admin/Manager Only"],
        description="Apagar disponibilidade de árbitro. Requer role MANAGER ou ADMIN."
    ),
)
class RefereeAvailabilityViewSet(viewsets.ModelViewSet):
    permission_classes = [IsManager, HasPermission]
    serializer_class = RefereeAvailabilitySerializer
    pagination_class = RefereePagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['referee', 'date', 'is_available']
    search_fields = ['referee__name']
    ordering_fields = ['date']

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return RefereeAvailability.objects.none()
        user = getattr(self.request, "user", None)
        tenant = getattr(user, "tenant", None)
        if not tenant:
            return RefereeAvailability.objects.none()
        return RefereeAvailability.objects.filter(tenant=tenant).select_related('referee').order_by('date', 'id')

    def perform_create(self, serializer):
        user = self.request.user
        tenant = getattr(user, "tenant", None)
        if not tenant:
            raise ValidationError({"detail": "Tenant não definido."})
        referee = serializer.validated_data.get("referee")
        if referee is None or referee.tenant_id != tenant.id:
            raise ValidationError({"referee": "Árbitro inválido."})
        serializer.save(tenant=tenant)
