from django.utils import timezone
from django.shortcuts import get_object_or_404

from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Notification
from .serializers import NotificationSerializer


class NotificationsListView(generics.ListAPIView):
    """List notifications for the authenticated user, newest first."""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).order_by('-created_at')


class UnreadCountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        count = (
            Notification.objects.filter(
                recipient=request.user, status=Notification.STATUS_PENDING
            ).count()
        )
        return Response({"unread_count": count})


class MarkReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        notif = get_object_or_404(Notification, pk=pk, recipient=request.user)
        notif.status = Notification.STATUS_SENT
        notif.delivered_at = timezone.now()
        notif.save(update_fields=["status", "delivered_at"])
        return Response(NotificationSerializer(notif).data, status=status.HTTP_200_OK)
