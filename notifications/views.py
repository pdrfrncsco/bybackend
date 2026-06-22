from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, extend_schema_view
from .models import Notification
from .serializers import NotificationSerializer

@extend_schema_view(
    list=extend_schema(
        tags=["Notifications"],
        description="Lista notificações do utilizador autenticado."
    ),
    retrieve=extend_schema(
        tags=["Notifications"],
        description="Detalhes de uma notificação do utilizador autenticado."
    ),
    destroy=extend_schema(
        tags=["Notifications"],
        description="Remove uma notificação do utilizador autenticado."
    ),
)
class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    @extend_schema(
        tags=["Notifications"],
        description="Marca uma notificação específica como lida para o utilizador autenticado."
    )
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        notification.read = True
        notification.save()
        return Response({'status': 'notification marked as read'})

    @action(detail=False, methods=['post'])
    @extend_schema(
        tags=["Notifications"],
        description="Marca todas as notificações do utilizador autenticado como lidas."
    )
    def mark_all_as_read(self, request):
        self.get_queryset().update(read=True)
        return Response({'status': 'all notifications marked as read'})
