from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
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
    GeneratedReportSerializer,
    ReportRequestSerializer,
)
from analytics.models import GeneratedReport
from analytics.permissions import CanViewTenantAnalytics, CanManageReports
from analytics.services.report_service import ReportService
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


class OrganizationDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsActiveAccount, CanViewTenantAnalytics]

    @extend_schema(
        tags=["analytics"],
        summary="Get organization dashboard analytics",
        parameters=[
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
        if tenant is None:
            tenant = OrganizationSelector.get_for_user(user=request.user)

        filters = DashboardFilterSerializer(data=request.query_params)
        filters.is_valid(raise_exception=True)
        validated = dict(filters.validated_data)

        payload = DashboardAnalyticsSelector.get_overview(
            tenant=tenant,
            period=validated.get("period", "all"),
            start_date=validated.get("start_date"),
            end_date=validated.get("end_date"),
        )
        return Response(DashboardOverviewSerializer(payload).data)


class ClubDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsActiveAccount, CanViewTenantAnalytics]

    @extend_schema(
        tags=["analytics"],
        summary="Get club dashboard analytics",
        parameters=[
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
    def get(self, request, club_id):
        tenant = getattr(request, "tenant", None)
        if tenant is None:
            tenant = OrganizationSelector.get_for_user(user=request.user)

        club_queryset = Club.objects.all()
        if tenant is not None:
            club_queryset = club_queryset.filter(tenant=tenant)
        club = club_queryset.filter(id=club_id).first()
        if club is None:
            return error_response(message="Club not found.", status_code=404)

        filters = DashboardFilterSerializer(data=request.query_params)
        filters.is_valid(raise_exception=True)
        validated = dict(filters.validated_data)

        payload = DashboardAnalyticsSelector.get_overview(
            tenant=tenant,
            club=club,
            period=validated.get("period", "all"),
            start_date=validated.get("start_date"),
            end_date=validated.get("end_date"),
        )
        return Response(DashboardOverviewSerializer(payload).data)


class CompetitionDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsActiveAccount, CanViewTenantAnalytics]

    @extend_schema(
        tags=["analytics"],
        summary="Get competition dashboard analytics",
        parameters=[
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
    def get(self, request, competition_id):
        tenant = getattr(request, "tenant", None)
        if tenant is None:
            tenant = OrganizationSelector.get_for_user(user=request.user)

        competition_queryset = Competition.objects.all()
        if tenant is not None:
            competition_queryset = competition_queryset.filter(tenant=tenant)
        competition = competition_queryset.filter(id=competition_id).first()
        if competition is None:
            return error_response(message="Competition not found.", status_code=404)

        filters = DashboardFilterSerializer(data=request.query_params)
        filters.is_valid(raise_exception=True)
        validated = dict(filters.validated_data)

        payload = DashboardAnalyticsSelector.get_overview(
            tenant=tenant,
            competition=competition,
            period=validated.get("period", "all"),
            start_date=validated.get("start_date"),
            end_date=validated.get("end_date"),
        )
        return Response(DashboardOverviewSerializer(payload).data)


class GeneratedReportListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsActiveAccount, CanManageReports]

    @extend_schema(
        tags=["analytics"],
        summary="List generated reports",
        responses={200: GeneratedReportSerializer(many=True)},
    )
    def get(self, request):
        tenant = getattr(request, "tenant", None)
        if tenant is None:
            tenant = OrganizationSelector.get_for_user(user=request.user)

        queryset = GeneratedReport.objects.all()
        if tenant:
            queryset = queryset.filter(tenant=tenant)
        else:
            queryset = queryset.filter(created_by=request.user)

        return Response(GeneratedReportSerializer(queryset, many=True).data)

    @extend_schema(
        tags=["analytics"],
        summary="Request report generation",
        request=ReportRequestSerializer,
        responses={201: GeneratedReportSerializer},
    )
    def post(self, request):
        tenant = getattr(request, "tenant", None)
        if tenant is None:
            tenant = OrganizationSelector.get_for_user(user=request.user)

        serializer = ReportRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data

        report = ReportService.request_report(
            tenant=tenant,
            name=validated["name"],
            report_type=validated["report_type"],
            format=validated["format"],
            filters=validated.get("filters", {}),
            created_by=request.user,
        )

        return Response(GeneratedReportSerializer(report).data, status=status.HTTP_201_CREATED)


class GeneratedReportDetailView(APIView):
    permission_classes = [IsAuthenticated, IsActiveAccount, CanManageReports]

    @extend_schema(
        tags=["analytics"],
        summary="Get generated report details",
        responses={200: GeneratedReportSerializer},
    )
    def get(self, request, pk):
        tenant = getattr(request, "tenant", None)
        if tenant is None:
            tenant = OrganizationSelector.get_for_user(user=request.user)

        queryset = GeneratedReport.objects.all()
        if tenant:
            queryset = queryset.filter(tenant=tenant)

        report = queryset.filter(id=pk).first()
        if report is None:
            return error_response(message="Report not found.", status_code=404)

        return Response(GeneratedReportSerializer(report).data)

    @extend_schema(
        tags=["analytics"],
        summary="Delete generated report",
        responses={204: None},
    )
    def delete(self, request, pk):
        tenant = getattr(request, "tenant", None)
        if tenant is None:
            tenant = OrganizationSelector.get_for_user(user=request.user)

        queryset = GeneratedReport.objects.all()
        if tenant:
            queryset = queryset.filter(tenant=tenant)

        report = queryset.filter(id=pk).first()
        if report is None:
            return error_response(message="Report not found.", status_code=404)

        if report.file:
            from media_assets.services.media_service import MediaAssetService
            try:
                MediaAssetService.delete_asset(asset_id=str(report.file.id))
            except Exception:
                pass

        report.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
