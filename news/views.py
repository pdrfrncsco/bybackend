from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from .models import NewsArticle, NewsArticleLike
from .serializers import NewsArticleSerializer
from core.permissions import IsManager, IsAdmin

@extend_schema_view(
    list=extend_schema(
        tags=["News"],
        description="Lista notícias internas do tenant. Requer utilizador autenticado."
    ),
    retrieve=extend_schema(
        tags=["News"],
        description="Detalhes de notícia interna do tenant. Requer utilizador autenticado."
    ),
    create=extend_schema(
        tags=["News", "Admin/Manager Only"],
        description="Cria notícia para o tenant actual. Requer role MANAGER ou ADMIN."
    ),
    update=extend_schema(
        tags=["News", "Admin/Manager Only"],
        description="Actualiza notícia. Requer role MANAGER ou ADMIN."
    ),
    partial_update=extend_schema(
        tags=["News", "Admin/Manager Only"],
        description="Actualiza parcialmente notícia. Requer role MANAGER ou ADMIN."
    ),
    destroy=extend_schema(
        tags=["News", "Admin/Manager Only"],
        description="Remove notícia. Requer role MANAGER ou ADMIN."
    ),
)
class NewsArticleViewSet(viewsets.ModelViewSet):
    serializer_class = NewsArticleSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'summary', 'content', 'author']
    ordering_fields = ['published_at', 'created_at']
    filterset_fields = ['category', 'status']

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.tenant:
            return NewsArticle.objects.filter(tenant=user.tenant)
        return NewsArticle.objects.none()

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.user.tenant)

@extend_schema_view(
    list=extend_schema(
        tags=["Public News"],
        description="Lista notícias públicas publicadas. Público (sem autenticação)."
    ),
    retrieve=extend_schema(
        tags=["Public News"],
        description="Detalhes de notícia pública. Público (sem autenticação)."
    ),
)
class PublicNewsViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NewsArticleSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'summary', 'content', 'author']
    ordering_fields = ['published_at']
    filterset_fields = ['category']

    def get_queryset(self):
        # Return only published news
        qs = NewsArticle.objects.filter(status='published')
        
        # Optional: Filter by tenant slug if provided in query params
        tenant_slug = self.request.query_params.get('tenant_slug')
        if tenant_slug:
            qs = qs.filter(tenant__slug=tenant_slug)
            
        return qs.order_by('-published_at')

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.views += 1
        instance.save(update_fields=['views'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    @extend_schema(
        tags=["Public News"],
        description="Regista um 'like' numa notícia pública. Requer utilizador autenticado."
    )
    def like(self, request, pk=None):
        instance = self.get_object()

        if not request.user or not request.user.is_authenticated:
            return Response(
                {'detail': 'Autenticação necessária para registar like.'},
                status=401
            )

        like, created = NewsArticleLike.objects.get_or_create(
            article=instance,
            user=request.user,
        )

        if created:
            instance.likes += 1
            instance.save(update_fields=['likes'])
            return Response({'status': 'liked', 'likes': instance.likes})

        return Response({'status': 'already_liked', 'likes': instance.likes})

    @action(detail=True, methods=['post'])
    @extend_schema(
        tags=["Public News"],
        description="Regista um 'share' de uma notícia pública. Público (sem autenticação)."
    )
    def share(self, request, pk=None):
        instance = self.get_object()
        instance.shares += 1
        instance.save(update_fields=['shares'])
        return Response({'status': 'shared', 'shares': instance.shares})
