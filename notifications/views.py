from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.pagination import StandardPagination

from .models import Notification
from .serializers import NotificationSerializer


class NotificationsListView(generics.ListAPIView):
    """List notifications for the authenticated user, newest first.

    Returns a wrapped, paginated ApiResponse object matching the standard
    list envelope used across the platform.
    """

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardPagination
    queryset = Notification.objects.none()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Notification.objects.none()
        return Notification.objects.filter(recipient=self.request.user).order_by("-created_at")


class UnreadCountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(recipient=request.user, status=Notification.STATUS_PENDING).count()
        return Response({"success": True, "message": "", "data": {"unread": count}})


class MarkReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        notif = get_object_or_404(Notification, pk=pk, recipient=request.user)
        notif.status = Notification.STATUS_SENT
        notif.delivered_at = timezone.now()
        notif.save(update_fields=["status", "delivered_at"])
        return Response(
            {"success": True, "message": "", "data": NotificationSerializer(notif).data}, status=status.HTTP_200_OK
        )
