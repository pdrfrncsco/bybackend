from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
from drf_spectacular.utils import extend_schema, extend_schema_view
from affiliations.models import ClubeOrganizacaoRequest, JogadorClubeRequest, JogadorHistoricoClube, RequestStatus
from affiliations.serializers import (
    ClubeOrganizacaoRequestSerializer,
    JogadorClubeRequestSerializer,
    JogadorHistoricoClubeSerializer,
)
from affiliations.selectors import (
    get_clube_organizacao_requests,
    get_jogador_clube_requests,
    get_jogador_historico_clubs,
)
from affiliations.services import (
    create_clube_organizacao_request,
    decide_clube_organizacao_request,
    create_jogador_clube_request,
    decide_jogador_clube_request,
)
from affiliations.permissions import CanManageClubeOrganizacaoRequest, CanManageJogadorClubeRequest
from accounts.models import UserRole


@extend_schema_view(
    list=extend_schema(tags=["Afiliações - Clube/Organização"], description="Lista todos os pedidos de afiliação de clube a organização."),
    retrieve=extend_schema(tags=["Afiliações - Clube/Organização"], description="Retorna os detalhes de um pedido específico."),
    create=extend_schema(tags=["Afiliações - Clube/Organização"], description="Submete um pedido de afiliação de clube."),
    decide=extend_schema(tags=["Afiliações - Clube/Organização"], description="Decide (aprova ou rejeita) um pedido pendente."),
)
class ClubeOrganizacaoRequestViewSet(viewsets.ModelViewSet):
    serializer_class = ClubeOrganizacaoRequestSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.IsAuthenticated, CanManageClubeOrganizacaoRequest]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['estado', 'clube', 'organizacao']
    ordering_fields = ['data_pedido', 'data_decisao']
    ordering = ['-data_pedido']

    def get_queryset(self):
        return get_clube_organizacao_requests()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        clube_profile = serializer.validated_data['clube']
        organizacao_profile = serializer.validated_data['organizacao']
        mensagem = serializer.validated_data.get('mensagem', '')

        # Regra: se não for admin, o clube deve pertencer ao utilizador logado
        is_admin = request.user.role in [UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.LEGACY_ADMIN] or request.user.is_superuser
        if not is_admin and clube_profile.user != request.user:
            return Response(
                {"detail": "Não tem permissão para solicitar afiliação em nome deste clube."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            req = create_clube_organizacao_request(
                clube_profile=clube_profile,
                organizacao_profile=organizacao_profile,
                mensagem=mensagem
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        output_serializer = self.get_serializer(req)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['POST'])
    def decide(self, request, pk=None):
        decisao = request.data.get('estado')
        mensagem_resposta = request.data.get('mensagem_resposta', '')

        if decisao not in [RequestStatus.APPROVED, RequestStatus.REJECTED]:
            return Response(
                {"detail": "Decisão inválida. Use APPROVED ou REJECTED."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            req = decide_clube_organizacao_request(
                request_id=pk,
                status=decisao,
                user_decisor=request.user,
                mensagem_resposta=mensagem_resposta
            )
        except (ValueError, PermissionError) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        output_serializer = self.get_serializer(req)
        return Response(output_serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    list=extend_schema(tags=["Afiliações - Jogador/Clube"], description="Lista todos os pedidos de ingresso de jogador a clube."),
    retrieve=extend_schema(tags=["Afiliações - Jogador/Clube"], description="Retorna os detalhes de um pedido específico."),
    create=extend_schema(tags=["Afiliações - Jogador/Clube"], description="Submete um pedido de ingresso de jogador a clube."),
    decide=extend_schema(tags=["Afiliações - Jogador/Clube"], description="Decide (aprova ou rejeita) um pedido pendente."),
)
class JogadorClubeRequestViewSet(viewsets.ModelViewSet):
    serializer_class = JogadorClubeRequestSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.IsAuthenticated, CanManageJogadorClubeRequest]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['estado', 'jogador', 'clube']
    ordering_fields = ['data_pedido', 'data_decisao']
    ordering = ['-data_pedido']

    def get_queryset(self):
        return get_jogador_clube_requests()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        jogador_profile = serializer.validated_data['jogador']
        clube_profile = serializer.validated_data['clube']
        mensagem = serializer.validated_data.get('mensagem', '')

        # Regra: se não for admin, o jogador deve pertencer ao utilizador logado
        is_admin = request.user.role in [UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.LEGACY_ADMIN] or request.user.is_superuser
        if not is_admin and jogador_profile.user != request.user:
            return Response(
                {"detail": "Não tem permissão para solicitar ingresso em nome deste jogador."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            req = create_jogador_clube_request(
                jogador_profile=jogador_profile,
                clube_profile=clube_profile,
                mensagem=mensagem
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        output_serializer = self.get_serializer(req)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['POST'])
    def decide(self, request, pk=None):
        decisao = request.data.get('estado')
        mensagem_resposta = request.data.get('mensagem_resposta', '')

        if decisao not in [RequestStatus.APPROVED, RequestStatus.REJECTED]:
            return Response(
                {"detail": "Decisão inválida. Use APPROVED ou REJECTED."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            req = decide_jogador_clube_request(
                request_id=pk,
                status=decisao,
                user_decisor=request.user,
                mensagem_resposta=mensagem_resposta
            )
        except (ValueError, PermissionError) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        output_serializer = self.get_serializer(req)
        return Response(output_serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    list=extend_schema(tags=["Afiliações - Histórico de Jogador"], description="Lista todo o histórico de afiliações de clubs de jogadores."),
    retrieve=extend_schema(tags=["Afiliações - Histórico de Jogador"], description="Retorna os detalhes de um histórico específico."),
)
class JogadorHistoricoClubeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = JogadorHistoricoClubeSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['jogador', 'clube']
    ordering_fields = ['data_inicio', 'data_fim']
    ordering = ['-data_inicio']

    def get_queryset(self):
        return get_jogador_historico_clubs()
