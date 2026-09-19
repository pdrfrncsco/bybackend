"""
BOLAYETU — Player Performance Serializers

Serializers for GPS and biometric performance metrics.
"""

from rest_framework import serializers
from players.models.performance import PlayerPerformanceMetric


class PlayerPerformanceMetricSerializer(serializers.ModelSerializer):
    """Serializer for PlayerPerformanceMetric."""

    metric_type_display = serializers.CharField(source="get_metric_type_display", read_only=True)
    source_display = serializers.CharField(source="get_source_display", read_only=True)

    class Meta:
        model = PlayerPerformanceMetric
        fields = [
            "id",
            "player",
            "match",
            "recorded_at",
            "metric_type",
            "metric_type_display",
            "value",
            "unit",
            "source",
            "source_display",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class PlayerPerformanceMetricGroupSerializer(serializers.Serializer):
    """Group of metrics by category with summary statistics."""

    category = serializers.CharField()
    metrics = PlayerPerformanceMetricSerializer(many=True)
    average = serializers.FloatField()
    max = serializers.FloatField()
    min = serializers.FloatField()


class PlayerPerformanceSummarySerializer(serializers.Serializer):
    """Aggregated performance summary across all metric categories."""

    speed_metrics = PlayerPerformanceMetricGroupSerializer()
    distance_metrics = PlayerPerformanceMetricGroupSerializer()
    physical_metrics = PlayerPerformanceMetricGroupSerializer()
    biometric_metrics = PlayerPerformanceMetricGroupSerializer()
    workload_metrics = PlayerPerformanceMetricGroupSerializer()
