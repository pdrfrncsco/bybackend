"""
BOLAYETU — Health Check Endpoints

Used by Docker, Nginx, GitHub Actions CD and monitoring (09_DEVOPS_ARCHITECTURE.md §22).
"""

from django.db import connection
from django.utils import timezone
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from common.responses import error_response, success_response


class HealthView(APIView):
    """Basic health check — confirms the API process is running."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        return success_response(
            data={"status": "ok", "timestamp": timezone.now().isoformat()},
            message="Service is healthy.",
        )


class LivenessView(APIView):
    """Liveness probe — process is alive (no dependency checks)."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        return success_response(
            data={"status": "alive"},
            message="Service is alive.",
        )


class ReadinessView(APIView):
    """Readiness probe — verifies database connectivity."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception as exc:
            return error_response(
                message=f"Service not ready: {exc}",
                errors={"database": "unavailable"},
                status_code=503,
            )

        return success_response(
            data={"status": "ready", "database": "ok"},
            message="Service is ready.",
        )
