from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from core.permissions import HasPermission, IsManager
from .models import Treinador, HistoricoTreinador
from .reporting import generate_treinador_report
from .serializers import (
    TreinadorSerializer,
    HistoricoTreinadorSerializer,
    HistoricoTreinadorCreateSerializer,
    EncerrarHistoricoTreinadorSerializer,
    LicencaTreinadorSerializer,
)


class TreinadorPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 100


class TreinadorViewSet(viewsets.ModelViewSet):
    serializer_class = TreinadorSerializer
    pagination_class = TreinadorPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['nacionalidade']
    search_fields = ['first_name', 'last_name']
    ordering_fields = ['first_name', 'last_name', 'data_nascimento', 'created_at']

    def get_permissions(self):
        if self.action in ["list", "retrieve", "historico", "relatorio"]:
            return [permissions.IsAuthenticated()]
        return [IsManager(), HasPermission()]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Treinador.objects.none()

        user = getattr(self.request, "user", None)
        tenant = getattr(user, "tenant", None)
        queryset = Treinador.objects.all().order_by('last_name', 'first_name', 'id')
        if tenant:
            queryset = queryset.filter(tenant=tenant)
        else:
            queryset = queryset.none()
        return queryset.prefetch_related('historico__clube', 'licencas')

    def perform_create(self, serializer):
        user = self.request.user
        if not getattr(user, "tenant", None):
            raise ValidationError({"detail": "Tenant não definido."})
        serializer.save(tenant=user.tenant)

    @action(detail=True, methods=["get", "post"], url_path="historico")
    def historico(self, request, pk=None):
        treinador = self.get_object()

        if request.method.lower() == "get":
            queryset = treinador.historico.select_related('clube').order_by('-data_inicio', '-created_at', 'id')
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = HistoricoTreinadorSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            serializer = HistoricoTreinadorSerializer(queryset, many=True)
            return Response(serializer.data)

        serializer = HistoricoTreinadorCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        clube = serializer.validated_data.get("clube")
        user = request.user
        tenant = getattr(user, "tenant", None)
        if not tenant:
            raise ValidationError({"detail": "Tenant não definido."})
        if treinador.tenant_id != tenant.id:
            raise ValidationError({"treinador": "Treinador inválido."})
        if getattr(clube, "tenant_id", None) != tenant.id:
            raise ValidationError({"clube": "Clube inválido."})

        with transaction.atomic():
            atual = HistoricoTreinador.objects.select_for_update().filter(
                treinador=treinador,
                data_fim__isnull=True,
            ).first()
            if atual is not None:
                raise ValidationError({"detail": "Já existe um histórico ativo. Encerre-o antes de criar outro."})

            historico = serializer.save(treinador=treinador)

        return Response(HistoricoTreinadorSerializer(historico).data, status=201)

    @action(detail=True, methods=["post"], url_path="historico/encerrar")
    def encerrar_historico(self, request, pk=None):
        treinador = self.get_object()
        serializer = EncerrarHistoricoTreinadorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data_fim = serializer.validated_data["data_fim"]

        with transaction.atomic():
            atual = HistoricoTreinador.objects.select_for_update().filter(
                treinador=treinador,
                data_fim__isnull=True,
            ).first()
            if atual is None:
                raise ValidationError({"detail": "Não existe histórico ativo para encerrar."})
            atual.data_fim = data_fim
            atual.save(update_fields=["data_fim", "updated_at"])

        return Response(HistoricoTreinadorSerializer(atual).data)

    @action(detail=True, methods=["get"], url_path="relatorio")
    @method_decorator(cache_page(30))
    def relatorio(self, request, pk=None):
        treinador = self.get_object()
        report = generate_treinador_report(treinador)
        return Response(report.to_dict())

    @action(detail=True, methods=["post"], url_path="licencas")
    def licencas(self, request, pk=None):
        treinador = self.get_object()
        user = request.user
        tenant = getattr(user, "tenant", None)
        if not tenant:
            raise ValidationError({"detail": "Tenant não definido."})
        if treinador.tenant_id != tenant.id:
            raise ValidationError({"treinador": "Treinador inválido."})

        serializer = LicencaTreinadorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        licenca = serializer.save(treinador=treinador)
        output = LicencaTreinadorSerializer(licenca)
        return Response(output.data, status=201)

