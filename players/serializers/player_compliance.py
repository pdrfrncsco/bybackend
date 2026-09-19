"""
BOLAYETU — Player Compliance Serializers

Serializers for FIFA RSTP regulatory compliance records.
"""

from rest_framework import serializers
from players.models.compliance import PlayerComplianceRecord


class PlayerComplianceRecordSerializer(serializers.ModelSerializer):
    """Full serializer for PlayerComplianceRecord."""

    rule_type_display = serializers.CharField(source="get_rule_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    priority_display = serializers.CharField(source="get_priority_display", read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    requires_action = serializers.BooleanField(read_only=True)

    class Meta:
        model = PlayerComplianceRecord
        fields = [
            "id",
            "player",
            "transfer",
            "rule_type",
            "rule_type_display",
            "rule_reference",
            "priority",
            "priority_display",
            "status",
            "status_display",
            "description",
            "notes",
            "resolution_notes",
            "exemption_reason",
            "deadline",
            "is_overdue",
            "requires_action",
            "reviewed_at",
            "reviewed_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class PlayerComplianceSummarySerializer(serializers.Serializer):
    """Summary of player compliance statistics."""

    total = serializers.IntegerField()
    compliant = serializers.IntegerField()
    non_compliant = serializers.IntegerField()
    pending_review = serializers.IntegerField()
    overdue = serializers.IntegerField()
    critical_issues = serializers.IntegerField()
