from rest_framework import viewsets, permissions, filters, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema, extend_schema_view

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
from accounts.models import (
    OrganizacaoProfile,
    ClubeProfile,
    JogadorProfile,
    AdeptoProfile,
    UserRole,
)
from accounts.serializers import (
    OrganizacaoProfileSerializer,
    ClubeProfileSerializer,
    JogadorProfileSerializer,
    AdeptoProfileSerializer,
)
from accounts.selectors import (
    get_organizacao_profiles,
    get_clube_profiles,
    get_jogador_profiles,
    get_adepto_profiles,
)
from accounts.services import (
    create_organizacao_profile,
    create_clube_profile,
    create_jogador_profile,
    create_adepto_profile,
)
from accounts.permissions import IsOwnerOrAdmin, IsAdminOrReadOnly


@extend_schema_view(
    list=extend_schema(tags=["Perfis - Organizações"], description="Lista todos os perfis de organizações."),
    retrieve=extend_schema(tags=["Perfis - Organizações"], description="Retorna os detalhes de um perfil de organização específico."),
    create=extend_schema(tags=["Perfis - Organizações"], description="Cria um perfil de organização para o utilizador autenticado."),
    update=extend_schema(tags=["Perfis - Organizações"], description="Atualiza um perfil de organização."),
    partial_update=extend_schema(tags=["Perfis - Organizações"], description="Atualiza parcialmente um perfil de organização."),
    destroy=extend_schema(tags=["Perfis - Organizações"], description="Remove um perfil de organização."),
)
class OrganizacaoProfileViewSet(viewsets.ModelViewSet):
    serializer_class = OrganizacaoProfileSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['pais', 'provincia', 'cidade', 'status']
    search_fields = ['nome', 'sigla', 'descricao']
    ordering_fields = ['nome', 'created_at']
    ordering = ['nome']

    def get_queryset(self):
        return get_organizacao_profiles()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # O utilizador dono do perfil será o autenticado, a menos que seja admin e especifique outro
        target_user = request.user
        is_admin = request.user.role in [UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.LEGACY_ADMIN] or request.user.is_superuser
        
        if is_admin and 'user' in serializer.validated_data:
            target_user = serializer.validated_data['user']

        profile = create_organizacao_profile(
            user=target_user,
            **{k: v for k, v in serializer.validated_data.items() if k != 'user'}
        )
        
        output_serializer = self.get_serializer(profile)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['GET', 'PUT', 'PATCH'])
    def me(self, request):
        try:
            profile = self.get_queryset().get(user=request.user)
        except OrganizacaoProfile.DoesNotExist:
            return Response({'detail': 'Perfil não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'GET':
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(tags=["Perfis - Clubs"], description="Lista todos os perfis de clubs."),
    retrieve=extend_schema(tags=["Perfis - Clubs"], description="Retorna os detalhes de um perfil de clube específico."),
    create=extend_schema(tags=["Perfis - Clubs"], description="Cria um perfil de clube para o utilizador autenticado."),
    update=extend_schema(tags=["Perfis - Clubs"], description="Atualiza um perfil de clube."),
    partial_update=extend_schema(tags=["Perfis - Clubs"], description="Atualiza parcialmente um perfil de clube."),
    destroy=extend_schema(tags=["Perfis - Clubs"], description="Remove um perfil de clube."),
)
class ClubeProfileViewSet(viewsets.ModelViewSet):
    serializer_class = ClubeProfileSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['estadio', 'cores']
    search_fields = ['nome', 'sigla', 'historia']
    ordering_fields = ['nome', 'fundacao', 'created_at']
    ordering = ['nome']

    def get_queryset(self):
        return get_clube_profiles()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        target_user = request.user
        is_admin = request.user.role in [UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.LEGACY_ADMIN] or request.user.is_superuser
        
        if is_admin and 'user' in serializer.validated_data:
            target_user = serializer.validated_data['user']

        profile = create_clube_profile(
            user=target_user,
            **{k: v for k, v in serializer.validated_data.items() if k != 'user'}
        )
        
        output_serializer = self.get_serializer(profile)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['GET', 'PUT', 'PATCH'])
    def me(self, request):
        try:
            profile = self.get_queryset().get(user=request.user)
        except ClubeProfile.DoesNotExist:
            return Response({'detail': 'Perfil não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'GET':
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(tags=["Perfis - Jogadores"], description="Lista todos os perfis de jogadores."),
    retrieve=extend_schema(tags=["Perfis - Jogadores"], description="Retorna os detalhes de um perfil de jogador específico."),
    create=extend_schema(tags=["Perfis - Jogadores"], description="Cria um perfil de jogador para o utilizador autenticado."),
    update=extend_schema(tags=["Perfis - Jogadores"], description="Atualiza um perfil de jogador."),
    partial_update=extend_schema(tags=["Perfis - Jogadores"], description="Atualiza parcialmente um perfil de jogador."),
    destroy=extend_schema(tags=["Perfis - Jogadores"], description="Remove um perfil de jogador."),
)
class JogadorProfileViewSet(viewsets.ModelViewSet):
    serializer_class = JogadorProfileSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['nacionalidade', 'pe_preferencial', 'posicao', 'agente']
    search_fields = ['nome_completo', 'nome_desportivo', 'biografia']
    ordering_fields = ['nome_completo', 'nome_desportivo', 'data_nascimento', 'created_at']
    ordering = ['nome_completo']

    def get_queryset(self):
        return get_jogador_profiles()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        target_user = request.user
        is_admin = request.user.role in [UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.LEGACY_ADMIN] or request.user.is_superuser
        
        if is_admin and 'user' in serializer.validated_data:
            target_user = serializer.validated_data['user']

        profile = create_jogador_profile(
            user=target_user,
            **{k: v for k, v in serializer.validated_data.items() if k != 'user'}
        )
        
        output_serializer = self.get_serializer(profile)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['GET', 'PUT', 'PATCH'])
    def me(self, request):
        try:
            profile = self.get_queryset().get(user=request.user)
        except JogadorProfile.DoesNotExist:
            return Response({'detail': 'Perfil não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'GET':
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(tags=["Perfis - Adeptos"], description="Lista todos os perfis de adeptos."),
    retrieve=extend_schema(tags=["Perfis - Adeptos"], description="Retorna os detalhes de um perfil de adepto específico."),
    create=extend_schema(tags=["Perfis - Adeptos"], description="Cria um perfil de adepto para o utilizador autenticado."),
    update=extend_schema(tags=["Perfis - Adeptos"], description="Atualiza um perfil de adepto."),
    partial_update=extend_schema(tags=["Perfis - Adeptos"], description="Atualiza parcialmente um perfil de adepto."),
    destroy=extend_schema(tags=["Perfis - Adeptos"], description="Remove um perfil de adepto."),
)
class AdeptoProfileViewSet(viewsets.ModelViewSet):
    serializer_class = AdeptoProfileSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['cidade', 'pais']
    search_fields = ['nome']
    ordering_fields = ['nome', 'created_at']
    ordering = ['nome']

    def get_queryset(self):
        return get_adepto_profiles()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        target_user = request.user
        is_admin = request.user.role in [UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.LEGACY_ADMIN] or request.user.is_superuser
        
        if is_admin and 'user' in serializer.validated_data:
            target_user = serializer.validated_data['user']

        profile = create_adepto_profile(
            user=target_user,
            **{k: v for k, v in serializer.validated_data.items() if k != 'user'}
        )
        
        output_serializer = self.get_serializer(profile)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['GET', 'PUT', 'PATCH'])
    def me(self, request):
        try:
            profile = self.get_queryset().get(user=request.user)
        except AdeptoProfile.DoesNotExist:
            return Response({'detail': 'Perfil não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'GET':
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
