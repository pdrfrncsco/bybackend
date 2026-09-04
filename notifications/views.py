import json
import time

from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model

from common.pagination import StandardPagination
from common.renderers import ServerSentEventsRenderer

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


User = get_user_model()


class NotificationStreamView(APIView):
    """Server-Sent Events endpoint for real-time notification updates.

    The browser EventSource API does not support custom headers, so JWT
    authentication is accepted via the ``token`` query parameter instead of
    the Authorization header.  The token is validated server-side; if invalid,
    the stream closes immediately with a single error event.

    Events emitted:
    - ``ping``      — heartbeat every 15 s (keeps the connection alive)
    - ``init``      — sent once on connect with unread count snapshot
    - ``update``    — pushed whenever the unread count changes
    - ``new_notification`` — pushed when a new notification arrives (last 5 s)
    """

    permission_classes = []  # Auth handled manually via query param
    renderer_classes = [ServerSentEventsRenderer]
    POLL_INTERVAL = 15  # seconds between checks

    def _authenticate_token(self, request):
        """Validate JWT from query param and return the User or None."""
        raw_token = request.GET.get("token")
        if not raw_token:
            return None
        try:
            validated = AccessToken(raw_token)
            return User.objects.get(pk=validated["user_id"])
        except (InvalidToken, TokenError, User.DoesNotExist):
            return None

    def _event(self, event_type: str, data: dict) -> str:
        """Format a single SSE message."""
        return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

    def _stream(self, user):
        """Generator that yields SSE messages until the client disconnects."""
        last_unread = -1
        last_check = timezone.now()

        # Emit initial snapshot immediately
        unread = Notification.objects.filter(
            recipient=user, status=Notification.STATUS_PENDING
        ).count()
        last_unread = unread
        yield self._event("init", {"unread": unread})

        while True:
            time.sleep(self.POLL_INTERVAL)
            now = timezone.now()

            # Check for new notifications since last poll
            new_notifs = list(
                Notification.objects.filter(
                    recipient=user,
                    created_at__gt=last_check,
                ).values("id", "type", "payload", "status", "created_at")
            )

            # Check unread count
            unread = Notification.objects.filter(
                recipient=user, status=Notification.STATUS_PENDING
            ).count()

            # Emit new notification events first
            for notif in new_notifs:
                notif["created_at"] = str(notif["created_at"])
                yield self._event("new_notification", notif)

            # Emit unread count update if changed
            if unread != last_unread:
                yield self._event("update", {"unread": unread})
                last_unread = unread

            # Always emit a heartbeat ping
            yield self._event("ping", {"ts": str(now)})
            last_check = now

    def get(self, request):
        user = self._authenticate_token(request)
        if user is None:
            # Return a single error event and close
            def _error():
                yield self._event("error", {"detail": "Authentication required."})

            return StreamingHttpResponse(
                _error(),
                content_type="text/event-stream",
                status=200,  # SSE must respond 200 for EventSource to receive events
            )

        response = StreamingHttpResponse(
            self._stream(user),
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"  # Disable nginx buffering
        return response
