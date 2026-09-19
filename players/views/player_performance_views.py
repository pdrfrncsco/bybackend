"""
BOLAYETU — Player Performance Views

API views for player GPS, physical, and biometric performance metrics.
"""

import uuid
from datetime import timedelta
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from common.responses import success_response, error_response
from players.models import Player
from players.models.performance import PlayerPerformanceMetric
from players.serializers.player_performance import (
    PlayerPerformanceMetricSerializer,
)


def _resolve_player(identifier):
    """Resolve player by UUID or slug."""
    try:
        val = uuid.UUID(str(identifier))
        return Player.objects.filter(id=val).first()
    except (ValueError, AttributeError):
        return Player.objects.filter(slug=identifier).first()


class PlayerPerformanceMetricListView(APIView):
    """
    GET /api/v1/players/{player_id}/performance-metrics/
    List performance metrics, optionally filtered by metric_type.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, player_id=None, slug=None):
        identifier = player_id or slug or self.kwargs.get("player_id") or self.kwargs.get("slug")
        player = _resolve_player(identifier)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        queryset = PlayerPerformanceMetric.objects.filter(player=player).order_by("-recorded_at")
        metric_type = request.query_params.get("metric_type")
        if metric_type:
            queryset = queryset.filter(metric_type=metric_type)

        serializer = PlayerPerformanceMetricSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PlayerPerformanceSummaryView(APIView):
    """
    GET /api/v1/players/{player_id}/performance/summary/
    Aggregated performance summary grouped by speed, distance, physical, biometric, workload.
    """

    permission_classes = [IsAuthenticated]

    CATEGORY_METRICS = {
        "speed_metrics": ["max_speed", "avg_speed", "sprint_speed"],
        "distance_metrics": ["total_distance", "sprint_distance", "high_speed_distance"],
        "physical_metrics": ["sprints_count", "accelerations", "decelerations", "jumps"],
        "biometric_metrics": ["max_heart_rate", "avg_heart_rate", "heart_rate_zones"],
        "workload_metrics": ["player_load", "training_load", "match_load", "recovery_time", "fatigue_index"],
    }

    def get(self, request, player_id=None, slug=None):
        identifier = player_id or slug or self.kwargs.get("player_id") or self.kwargs.get("slug")
        player = _resolve_player(identifier)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        metrics = list(PlayerPerformanceMetric.objects.filter(player=player).order_by("-recorded_at"))

        result = {}
        for group_name, types in self.CATEGORY_METRICS.items():
            group_metrics = [m for m in metrics if m.metric_type in types]
            values = [float(m.value) for m in group_metrics if m.value is not None]

            serialized_metrics = PlayerPerformanceMetricSerializer(group_metrics, many=True).data
            avg_val = round(sum(values) / len(values), 2) if values else 0.0
            max_val = max(values) if values else 0.0
            min_val = min(values) if values else 0.0

            result[group_name] = {
                "category": group_name.replace("_metrics", ""),
                "metrics": serialized_metrics,
                "average": avg_val,
                "max": max_val,
                "min": min_val,
            }

        return Response(result, status=status.HTTP_200_OK)


class PlayerPerformanceTrendsView(APIView):
    """
    GET /api/v1/players/{player_id}/performance/trends/?days=30
    Trends in performance over the specified time window.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, player_id=None, slug=None):
        identifier = player_id or slug or self.kwargs.get("player_id") or self.kwargs.get("slug")
        player = _resolve_player(identifier)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        try:
            days = int(request.query_params.get("days", 30))
        except (ValueError, TypeError):
            days = 30

        since = timezone.now() - timedelta(days=days)
        metrics = PlayerPerformanceMetric.objects.filter(
            player=player,
            recorded_at__gte=since,
        ).order_by("recorded_at")

        serializer = PlayerPerformanceMetricSerializer(metrics, many=True)
        return Response(
            {
                "days": days,
                "count": metrics.count(),
                "trends": serializer.data,
            },
            status=status.HTTP_200_OK,
        )
