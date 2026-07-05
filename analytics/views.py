from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsActiveAccount
from accounts.selectors import TenantMembershipSelector
from analytics.selectors import DashboardAnalyticsSelector
from analytics.serializers import (
    DashboardFilterSerializer,
    DashboardOverviewSerializer,
    PublicStatsSerializer,
)
from clubs.models import Club
from common.responses import error_response
from competitions.models import Competition
from organizations.selectors import OrganizationSelector


class DashboardOverviewView(APIView):
    permission_classes = [IsAuthenticated, IsActiveAccount]

    @extend_schema(
        tags=["analytics"],
        summary="Get dashboard overview analytics",
        parameters=[
            OpenApiParameter("competition_id", OpenApiTypes.UUID, OpenApiParameter.QUERY, required=False),
            OpenApiParameter("club_id", OpenApiTypes.UUID, OpenApiParameter.QUERY, required=False),
            OpenApiParameter(
                "period",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                required=False,
                enum=["all", "7d", "30d", "90d", "365d", "season"],
            ),
            OpenApiParameter("start_date", OpenApiTypes.DATE, OpenApiParameter.QUERY, required=False),
            OpenApiParameter("end_date", OpenApiTypes.DATE, OpenApiParameter.QUERY, required=False),
        ],
        responses={200: DashboardOverviewSerializer},
    )
    def get(self, request):
        tenant = getattr(request, "tenant", None)

        if tenant and not (request.user.is_staff or request.user.is_superuser):
            membership = TenantMembershipSelector.get_membership(
                user=request.user,
                tenant_id=tenant.id,
            )
            if membership is None or not membership.is_active:
                return error_response(
                    message="You do not belong to this organization.",
                    status_code=403,
                )

        if tenant is None:
            tenant = OrganizationSelector.get_for_user(user=request.user)

        filters = DashboardFilterSerializer(data=request.query_params)
        filters.is_valid(raise_exception=True)
        validated = dict(filters.validated_data)

        competition = None
        competition_id = validated.get("competition_id")
        if competition_id:
            competition_queryset = Competition.objects.all()
            if tenant is not None:
                competition_queryset = competition_queryset.filter(tenant=tenant)
            competition = competition_queryset.filter(id=competition_id).first()
            if competition is None:
                return error_response(message="Competition not found.", status_code=404)

        club = None
        club_id = validated.get("club_id")
        if club_id:
            club_queryset = Club.objects.all()
            if tenant is not None:
                club_queryset = club_queryset.filter(tenant=tenant)
            club = club_queryset.filter(id=club_id).first()
            if club is None:
                return error_response(message="Club not found.", status_code=404)

        payload = DashboardAnalyticsSelector.get_overview(
            tenant=tenant,
            competition=competition,
            club=club,
            period=validated.get("period", "all"),
            start_date=validated.get("start_date"),
            end_date=validated.get("end_date"),
        )
        return Response(DashboardOverviewSerializer(payload).data)


class PublicStatsView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["analytics"],
        summary="Get public ecosystem stats",
        responses={200: PublicStatsSerializer},
    )
    def get(self, request):
        payload = DashboardAnalyticsSelector.get_public_stats()
        return Response(PublicStatsSerializer(payload).data)
