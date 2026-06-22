from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db import models
from drf_spectacular.utils import extend_schema, extend_schema_view
from .models import Advertisement
from .serializers import AdvertisementSerializer
from core.permissions import HasPermission


import logging

logger = logging.getLogger(__name__)

class IsAdsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        from accounts.models import UserRole
        return request.user.role in [
            UserRole.SUPERADMIN,
            UserRole.ADS_MANAGER,
            UserRole.ADMIN,
            UserRole.LEGACY_ADMIN,
            'superadmin',
            'ads_manager',
        ] or request.user.is_superuser


@extend_schema_view(
    list=extend_schema(
        tags=["Advertisements"],
        description="Lista campanhas de publicidade. Público: vê apenas ativas. Admin/Manager: vê todas."
    ),
    retrieve=extend_schema(
        tags=["Advertisements"],
        description="Detalhes de campanha de publicidade. Público: vê apenas ativas. Admin/Manager: vê todas."
    ),
    create=extend_schema(
        tags=["Advertisements", "Admin Only"],
        description="Cria campanha de publicidade. Requer Superadmin ou Ads Manager."
    ),
    update=extend_schema(
        tags=["Advertisements", "Admin Only"],
        description="Actualiza campanha de publicidade. Requer Superadmin ou Ads Manager."
    ),
    partial_update=extend_schema(
        tags=["Advertisements", "Admin Only"],
        description="Actualiza parcialmente campanha de publicidade. Requer Superadmin ou Ads Manager."
    ),
    destroy=extend_schema(
        tags=["Advertisements", "Admin Only"],
        description="Remove campanha de publicidade. Requer Superadmin ou Ads Manager."
    ),
)
class AdvertisementViewSet(viewsets.ModelViewSet):
    serializer_class = AdvertisementSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'client_name']
    ordering_fields = ['created_at', 'impressions', 'clicks']
    filterset_fields = ['placement', 'status']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'impression', 'click']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsAdsAdmin()]

    def get_queryset(self):
        user = self.request.user
        
        # Se for admin de ads, vê tudo
        from accounts.models import UserRole
        ads_roles = [UserRole.SUPERADMIN, UserRole.ADS_MANAGER, UserRole.ADMIN, UserRole.LEGACY_ADMIN, 'superadmin', 'ads_manager']
        if user.is_authenticated and (user.role in ads_roles or user.is_superuser):
            return Advertisement.objects.all()
            
        # Para leitura pública, retorna apenas ativos
        if self.action in ['list', 'retrieve']:
            return Advertisement.objects.filter(status='active')
            
        # Para outras ações (que seriam bloqueadas por permissão de qualquer forma), retorna vazio
        return Advertisement.objects.none()

    def perform_create(self, serializer):
        # Permite criar sem tenant (global)
        instance = serializer.save()
        user = self.request.user
        logger.info(f"Advertisement created: {instance.id} by user {user.id} ({user.email})")

    def perform_update(self, serializer):
        instance = serializer.save()
        user = self.request.user
        logger.info(f"Advertisement updated: {instance.id} by user {user.id} ({user.email})")

    def perform_destroy(self, instance):
        user = self.request.user
        logger.info(f"Advertisement deleted: {instance.id} by user {user.id} ({user.email})")
        instance.delete()

    @action(detail=True, methods=['post'], permission_classes=[permissions.AllowAny])
    @extend_schema(
        tags=["Advertisements", "Public"],
        description="Regista uma impressão de anúncio. Público (sem autenticação)."
    )
    def impression(self, request, pk=None):
        advertisement = Advertisement.objects.filter(pk=pk).first()
        if not advertisement:
            return Response(status=status.HTTP_404_NOT_FOUND)
        Advertisement.objects.filter(pk=pk).update(impressions=models.F('impressions') + 1)
        advertisement.refresh_from_db(fields=['impressions', 'clicks'])
        serializer = self.get_serializer(advertisement)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[permissions.AllowAny])
    @extend_schema(
        tags=["Advertisements", "Public"],
        description="Regista um clique em anúncio. Público (sem autenticação)."
    )
    def click(self, request, pk=None):
        advertisement = Advertisement.objects.filter(pk=pk).first()
        if not advertisement:
            return Response(status=status.HTTP_404_NOT_FOUND)
        Advertisement.objects.filter(pk=pk).update(clicks=models.F('clicks') + 1)
        advertisement.refresh_from_db(fields=['impressions', 'clicks'])
        serializer = self.get_serializer(advertisement)
        return Response(serializer.data, status=status.HTTP_200_OK)
