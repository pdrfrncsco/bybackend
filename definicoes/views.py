from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import TenantSettings
from .serializers import TenantSettingsSerializer


@extend_schema_view(
    list=extend_schema(
        tags=["Tenant Settings", "Admin/Manager Only"],
        description="Lista definições do tenant actual. Requer utilizador autenticado com acesso ao tenant."
    ),
    retrieve=extend_schema(
        tags=["Tenant Settings", "Admin/Manager Only"],
        description="Detalhes de uma definição de tenant. Requer utilizador autenticado com acesso ao tenant."
    ),
    create=extend_schema(
        tags=["Tenant Settings", "Admin/Manager Only"],
        description="Cria definições para o tenant actual. Requer utilizador autenticado com acesso ao tenant."
    ),
    update=extend_schema(
        tags=["Tenant Settings", "Admin/Manager Only"],
        description="Actualiza definições do tenant actual. Requer utilizador autenticado com acesso ao tenant."
    ),
    partial_update=extend_schema(
        tags=["Tenant Settings", "Admin/Manager Only"],
        description="Actualiza parcialmente definições do tenant actual. Requer utilizador autenticado com acesso ao tenant."
    ),
    destroy=extend_schema(
        tags=["Tenant Settings", "Admin/Manager Only"],
        description="Remove definições do tenant actual. Requer utilizador autenticado com acesso ao tenant."
    ),
)
class TenantSettingsViewSet(viewsets.ModelViewSet):
    serializer_class = TenantSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        tenant = getattr(self.request.user, 'tenant', None)
        if tenant is None:
            return TenantSettings.objects.none()
        return TenantSettings.objects.filter(tenant=tenant)

    def perform_create(self, serializer):
        tenant = getattr(self.request.user, 'tenant', None)
        serializer.save(tenant=tenant)

    @action(detail=False, methods=['get', 'put', 'patch'], url_path='me')
    @extend_schema(
        tags=["Tenant Settings", "Admin/Manager Only"],
        description="Lê ou actualiza as definições do tenant associado ao utilizador autenticado."
    )
    def me(self, request):
        tenant = getattr(request.user, 'tenant', None)
        if tenant is None:
            return Response(
                {'detail': 'Tenant não definido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        settings_obj, _created = TenantSettings.objects.get_or_create(tenant=tenant)

        if request.method in ['PUT', 'PATCH']:
            serializer = self.get_serializer(
                settings_obj,
                data=request.data,
                partial=(request.method == 'PATCH'),
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        serializer = self.get_serializer(settings_obj)
        return Response(serializer.data)
