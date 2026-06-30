"""
BOLAYETU — Organization Views

API endpoints for organization management.

Endpoints:
    Authenticated (organization admin):
        GET    /api/v1/organizations/me/              — Get own organization
        PATCH  /api/v1/organizations/me/              — Update own organization
        POST   /api/v1/organizations/me/logo/         — Upload logo
        POST   /api/v1/organizations/me/launch/       — Launch portal after onboarding
        GET    /api/v1/organizations/me/onboarding-status/ — Onboarding gate status

    Public (anyone):
        GET    /api/v1/organizations/public/           — List public organizations
        GET    /api/v1/organizations/public/:slug/     — Get public org details
        GET    /api/v1/organizations/public/:slug/kpis/      — Get KPIs
        GET    /api/v1/organizations/public/:slug/history/   — Get tournament history
        GET    /api/v1/organizations/public/:slug/tournaments/ — Get tournaments
        GET    /api/v1/organizations/public/:slug/clubs/      — Get clubs

    Authenticated (any user):
        POST   /api/v1/organizations/public/:slug/subscribe/    — Subscribe
        POST   /api/v1/organizations/public/:slug/unsubscribe/  — Unsubscribe
"""

import logging

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema

from accounts.permissions import IsActiveAccount
from common.responses import success_response, created_response, error_response
from core.models import Tenant
from organizations.exceptions import (
    OrganizationNotFound,
    NoOrganizationMembership,
    NotOrganizationAdmin,
)
from organizations.permissions import (
    IsOrganizationAdmin,
)
from organizations.selectors import OrganizationSelector
from organizations.services import OrganizationService
from organizations.serializers import (
    OrganizationSerializer,
    OrganizationUpdateSerializer,
    PublicOrganizationSerializer,
    OrganizationKpisSerializer,
    OrganizationHistoryEntrySerializer,
    SubscriptionResponseSerializer,
    OnboardingStatusSerializer,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────
# Authenticated Organization Management (Admin)
# ─────────────────────────────────────────────────────────────────────


class OrganizationMeView(APIView):
    """
    Retrieve or update the authenticated user's organization.
    """

    permission_classes = [IsAuthenticated, IsActiveAccount]

    @extend_schema(
        tags=["organizations"],
        responses={200: OrganizationSerializer},
    )
    def get(self, request):
        tenant = OrganizationService.get_organization_for_user(user=request.user)
        serializer = OrganizationSerializer(tenant)
        return success_response(
            data=serializer.data,
            message="Organization retrieved successfully.",
        )

    @extend_schema(
        tags=["organizations"],
        request=OrganizationUpdateSerializer,
        responses={200: OrganizationSerializer},
    )
    def patch(self, request):
        tenant = OrganizationService.get_organization_for_user(user=request.user)

        # Verify admin privileges
        OrganizationService.assert_is_organization_admin(user=request.user, tenant=tenant)

        serializer = OrganizationUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        tenant = OrganizationService.update_organization(
            tenant=tenant,
            **serializer.validated_data,
        )

        return success_response(
            data=OrganizationSerializer(tenant).data,
            message="Organization updated successfully.",
        )


class OrganizationLogoView(APIView):
    """
    Upload a logo for the authenticated user's organization.
    """

    permission_classes = [IsAuthenticated, IsActiveAccount, IsOrganizationAdmin]

    @extend_schema(
        tags=["organizations"],
        request={"multipart/form-data": None},
        responses={200: OrganizationSerializer},
    )
    def post(self, request):
        tenant = OrganizationService.get_organization_for_user(user=request.user)

        file = request.FILES.get("logo")
        if not file:
            return error_response(
                message="No logo file provided.",
                status_code=400,
            )

        tenant = OrganizationService.upload_logo(tenant=tenant, file=file)

        return success_response(
            data=OrganizationSerializer(tenant).data,
            message="Logo uploaded successfully.",
        )


class OrganizationLaunchView(APIView):
    """
    Launch the organization portal after onboarding is complete.
    """

    permission_classes = [IsAuthenticated, IsActiveAccount, IsOrganizationAdmin]

    @extend_schema(tags=["organizations"])
    def post(self, request):
        tenant = OrganizationService.get_organization_for_user(user=request.user)
        OrganizationService.assert_is_organization_admin(user=request.user, tenant=tenant)

        result = OrganizationService.launch_portal(tenant=tenant)

        return success_response(
            data={
                "organization": OrganizationSerializer(result["tenant"]).data,
                "competitions_activated": result["competitions_activated"],
                "portal_url": result["portal_url"],
            },
            message="Portal launched successfully.",
        )


class OrganizationOnboardingStatusView(APIView):
    """
    Return onboarding gate status for the authenticated user's organization.
    """

    permission_classes = [IsAuthenticated, IsActiveAccount]

    @extend_schema(tags=["organizations"], responses={200: OnboardingStatusSerializer})
    def get(self, request):
        from competitions.selectors import CompetitionSelector

        tenant = OrganizationSelector.get_for_user(user=request.user)

        if tenant is None:
            return success_response(
                data={
                    "onboarding_required": False,
                    "has_organization": False,
                    "is_organization_admin": False,
                    "competitions_count": 0,
                    "organization": None,
                },
                message="Onboarding status retrieved successfully.",
            )

        is_admin = False
        try:
            OrganizationService.assert_is_organization_admin(
                user=request.user,
                tenant=tenant,
            )
            is_admin = True
        except NotOrganizationAdmin:
            is_admin = False

        competitions = CompetitionSelector.list_for_tenant(tenant=tenant)
        onboarding_required = (
            tenant.status == Tenant.TenantStatus.PENDING and is_admin
        )

        return success_response(
            data={
                "onboarding_required": onboarding_required,
                "has_organization": True,
                "is_organization_admin": is_admin,
                "competitions_count": len(competitions),
                "organization": OrganizationSerializer(tenant).data,
            },
            message="Onboarding status retrieved successfully.",
        )


# ─────────────────────────────────────────────────────────────────────
# Public Organization Endpoints
# ─────────────────────────────────────────────────────────────────────


class OrganizationPublicListView(APIView):
    """
    List all public, active organizations.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        tags=["organizations"],
        responses={200: PublicOrganizationSerializer(many=True)},
    )
    def get(self, request):
        search = request.query_params.get("search")
        org_type = request.query_params.get("type")

        queryset = OrganizationSelector.list_public(search=search, org_type=org_type)

        # Annotate with subscriber count to avoid N+1
        from django.db.models import Count, Q
        queryset = queryset.annotate(
            _subscriber_count=Count(
                "subscriptions",
                filter=Q(subscriptions__is_active=True),
            )
        )

        serializer = PublicOrganizationSerializer(queryset, many=True)
        return success_response(
            data=serializer.data,
            message="Public organizations retrieved successfully.",
        )


class OrganizationPublicDetailView(APIView):
    """
    Retrieve details of a public organization by slug.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        tags=["organizations"],
        responses={200: PublicOrganizationSerializer},
    )
    def get(self, request, slug: str):
        tenant = OrganizationSelector.get_by_slug(slug=slug)

        if tenant is None:
            raise OrganizationNotFound()

        serializer = PublicOrganizationSerializer(tenant)
        return success_response(
            data=serializer.data,
            message="Organization retrieved successfully.",
        )


class OrganizationKpisView(APIView):
    """
    Retrieve KPI statistics for a public organization.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        tags=["organizations"],
        responses={200: OrganizationKpisSerializer},
    )
    def get(self, request, slug: str):
        tenant = OrganizationSelector.get_by_slug(slug=slug)

        if tenant is None:
            raise OrganizationNotFound()

        kpis = OrganizationSelector.get_kpis(tenant=tenant)
        serializer = OrganizationKpisSerializer(kpis)
        return success_response(
            data=serializer.data,
            message="Organization KPIs retrieved successfully.",
        )


class OrganizationHistoryView(APIView):
    """
    Retrieve tournament history for a public organization.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        tags=["organizations"],
        responses={200: OrganizationHistoryEntrySerializer(many=True)},
    )
    def get(self, request, slug: str):
        tenant = OrganizationSelector.get_by_slug(slug=slug)

        if tenant is None:
            raise OrganizationNotFound()

        history = OrganizationSelector.get_history(tenant=tenant)
        serializer = OrganizationHistoryEntrySerializer(history, many=True)
        return success_response(
            data=serializer.data,
            message="Organization history retrieved successfully.",
        )


class OrganizationTournamentsView(APIView):
    """
    Retrieve tournaments for a public organization.
    """

    permission_classes = [AllowAny]

    @extend_schema(tags=["organizations"])
    def get(self, request, slug: str):
        tenant = OrganizationSelector.get_by_slug(slug=slug)

        if tenant is None:
            raise OrganizationNotFound()

        tournaments = OrganizationSelector.get_tournaments(tenant=tenant)
        return success_response(
            data=tournaments,
            message="Organization tournaments retrieved successfully.",
        )


class OrganizationClubsView(APIView):
    """
    Retrieve clubs affiliated with a public organization.
    """

    permission_classes = [AllowAny]

    @extend_schema(tags=["organizations"])
    def get(self, request, slug: str):
        tenant = OrganizationSelector.get_by_slug(slug=slug)

        if tenant is None:
            raise OrganizationNotFound()

        clubs = OrganizationSelector.get_clubs(tenant=tenant)
        return success_response(
            data=clubs,
            message="Organization clubs retrieved successfully.",
        )


# ─────────────────────────────────────────────────────────────────────
# Subscription Endpoints
# ─────────────────────────────────────────────────────────────────────


class OrganizationSubscribeView(APIView):
    """
    Subscribe the authenticated user to a public organization.
    """

    permission_classes = [IsAuthenticated, IsActiveAccount]

    @extend_schema(
        tags=["organizations"],
        responses={200: SubscriptionResponseSerializer},
    )
    def post(self, request, slug: str):
        tenant = OrganizationSelector.get_by_slug(slug=slug)

        if tenant is None:
            raise OrganizationNotFound()

        OrganizationService.subscribe(user=request.user, tenant=tenant)

        return success_response(
            data={
                "subscribed": True,
                "organization_id": str(tenant.id),
            },
            message="Subscribed successfully.",
        )


class OrganizationUnsubscribeView(APIView):
    """
    Unsubscribe the authenticated user from a public organization.
    """

    permission_classes = [IsAuthenticated, IsActiveAccount]

    @extend_schema(
        tags=["organizations"],
        responses={200: SubscriptionResponseSerializer},
    )
    def post(self, request, slug: str):
        tenant = OrganizationSelector.get_by_slug(slug=slug)

        if tenant is None:
            raise OrganizationNotFound()

        OrganizationService.unsubscribe(user=request.user, tenant=tenant)

        return success_response(
            data={
                "subscribed": False,
                "organization_id": str(tenant.id),
            },
            message="Unsubscribed successfully.",
        )
