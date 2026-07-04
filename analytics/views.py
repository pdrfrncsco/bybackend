from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsActiveAccount
from accounts.selectors import TenantMembershipSelector
from analytics.selectors import DashboardAnalyticsSelector
from analytics.serializers import DashboardOverviewSerializer, PublicStatsSerializer
from common.responses import error_response
from organizations.selectors import OrganizationSelector


class DashboardOverviewView(APIView):
    permission_classes = [IsAuthenticated, IsActiveAccount]

    @extend_schema(
        tags=["analytics"],
        summary="Get dashboard overview analytics",
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

        payload = DashboardAnalyticsSelector.get_overview(tenant=tenant)
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
