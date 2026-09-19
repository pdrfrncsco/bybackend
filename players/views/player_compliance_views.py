"""
BOLAYETU — Player Compliance Views

API views for FIFA RSTP compliance records and status summary.
"""

import uuid
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from common.responses import success_response, error_response
from players.models import Player
from players.models.compliance import PlayerComplianceRecord
from players.serializers.player_compliance import (
    PlayerComplianceRecordSerializer,
    PlayerComplianceSummarySerializer,
)


def _resolve_player(identifier):
    """Resolve player by UUID or slug."""
    try:
        val = uuid.UUID(str(identifier))
        return Player.objects.filter(id=val).first()
    except (ValueError, AttributeError):
        return Player.objects.filter(slug=identifier).first()


class PlayerComplianceRecordListView(APIView):
    """
    GET /api/v1/players/{player_id}/compliance/
    List regulatory compliance records for a player.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, player_id=None, slug=None):
        identifier = player_id or slug or self.kwargs.get("player_id") or self.kwargs.get("slug")
        player = _resolve_player(identifier)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        records = PlayerComplianceRecord.objects.filter(player=player).order_by("-created_at")
        serializer = PlayerComplianceRecordSerializer(records, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PlayerComplianceSummaryView(APIView):
    """
    GET /api/v1/players/{player_id}/compliance/status/
    Summary of compliance counts (compliant, overdue, critical, etc.).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, player_id=None, slug=None):
        identifier = player_id or slug or self.kwargs.get("player_id") or self.kwargs.get("slug")
        player = _resolve_player(identifier)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        records = list(PlayerComplianceRecord.objects.filter(player=player))
        total = len(records)
        compliant = sum(1 for r in records if r.status == PlayerComplianceRecord.ComplianceStatus.COMPLIANT)
        non_compliant = sum(1 for r in records if r.status == PlayerComplianceRecord.ComplianceStatus.NON_COMPLIANT)
        pending_review = sum(1 for r in records if r.status == PlayerComplianceRecord.ComplianceStatus.PENDING_REVIEW)
        overdue = sum(1 for r in records if r.is_overdue)
        critical_issues = sum(
            1
            for r in records
            if r.priority == PlayerComplianceRecord.Priority.CRITICAL
            and r.status != PlayerComplianceRecord.ComplianceStatus.COMPLIANT
        )

        data = {
            "total": total,
            "compliant": compliant,
            "non_compliant": non_compliant,
            "pending_review": pending_review,
            "overdue": overdue,
            "critical_issues": critical_issues,
        }
        return Response(data, status=status.HTTP_200_OK)
