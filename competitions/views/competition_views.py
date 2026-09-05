import logging

from django.db.models import Q
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from accounts.permissions import IsActiveAccount
from common.pagination import StandardPagination
from common.responses import created_response, error_response, not_found_response, success_response
from competitions.exceptions import CompetitionNotFound, DuplicateCompetition
from competitions.selectors import CompetitionSelector
from competitions.serializers import (
    CompetitionConfigSerializer,
    CompetitionCreateSerializer,
    CompetitionSerializer,
    CompetitionUpdateSerializer,
)
from competitions.services import CompetitionService
from organizations.permissions import IsOrganizationAdmin
from organizations.services import OrganizationService

logger = logging.getLogger(__name__)


class CompetitionListCreateView(APIView):
    """
    GET  → public: list all competitions.
    POST → org admin only: create a competition.
    """

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated(), IsActiveAccount(), IsOrganizationAdmin()]

    @extend_schema(tags=["competitions"], responses={200: CompetitionSerializer(many=True)})
    def get(self, request):
        competitions = CompetitionSelector.list_all_active(
            tenant=getattr(request, "tenant", None),
        )

        paginator = StandardPagination()
        page = paginator.paginate_queryset(competitions, request)
        serializer = CompetitionSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        tags=["competitions"],
        request=CompetitionCreateSerializer,
        responses={201: CompetitionSerializer},
    )
    def post(self, request):
        tenant = OrganizationService.get_organization_for_user(user=request.user)
        OrganizationService.assert_is_organization_admin(user=request.user, tenant=tenant)

        serializer = CompetitionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            competition = CompetitionService.create_competition(
                tenant=tenant,
                **serializer.validated_data,
            )
        except DuplicateCompetition:
            return error_response(
                message="A competition with this name and season already exists.",
                status_code=400,
            )

        return created_response(
            data=CompetitionSerializer(competition).data,
            message="Competition created successfully.",
        )


class CompetitionDetailView(APIView):
    """
    GET   → public: retrieve a competition by ID or slug.
    PATCH → org admin only: update competition fields.
    """

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated(), IsActiveAccount(), IsOrganizationAdmin()]

    @extend_schema(tags=["competitions"], responses={200: CompetitionSerializer})
    def get(self, request, competition_id):
        tenant = getattr(request, "tenant", None)
        # Use selector that now accepts both slug and UUID
        competition = CompetitionSelector.get_by_id_public(
            competition_id=competition_id,
            tenant=tenant,
        )
        if competition is None:
            return not_found_response(message="Competition not found.")
        return success_response(
            data=CompetitionSerializer(competition).data,
            message="Competition retrieved successfully.",
        )

    @extend_schema(
        tags=["competitions"],
        request=CompetitionUpdateSerializer,
        responses={200: CompetitionSerializer},
    )
    def patch(self, request, competition_id):
        tenant = OrganizationService.get_organization_for_user(user=request.user)
        OrganizationService.assert_is_organization_admin(user=request.user, tenant=tenant)

        try:
            competition = CompetitionService.get_competition_for_tenant(
                tenant=tenant,
                competition_id=competition_id,
            )
        except CompetitionNotFound:
            return not_found_response(message="Competition not found.")

        serializer = CompetitionUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        competition = CompetitionService.update_competition(
            competition=competition,
            **serializer.validated_data,
        )


class ClubCompetitionListView(APIView):
    """
    GET /api/v1/clubs/{club_id}/competitions/
    List competitions that a club is registered in.
    """

    permission_classes = [IsAuthenticated, IsActiveAccount]

    @extend_schema(
        tags=["competitions"],
        responses={200: CompetitionSerializer(many=True)},
    )
    def get(self, request, club_id):
        from clubs.models import Club
        from competitions.models import CompetitionRegistration
        from competitions.constants import CompetitionStatus

        try:
            club = Club.objects.get(pk=club_id)
        except Club.DoesNotExist:
            return not_found_response(message="Club not found.")

        # Get competitions that the club is registered in and are active
        competitions = CompetitionRegistration.objects.filter(
            club=club,
            competition__status=CompetitionStatus.ACTIVE
        ).select_related("competition").values_list("competition", flat=True)

        # We need to get the actual Competition objects
        from competitions.models import Competition
        competition_objs = Competition.objects.filter(id__in=competitions)

        serializer = CompetitionSerializer(competition_objs, many=True)
        return success_response(
            data=serializer.data,
            message="Competitions for this club retrieved successfully.",
        )


class CompetitionConfigView(APIView):
    """
    GET   → organization admin only: retrieve competition configuration.
    PATCH → organization admin only: update competition configuration.
    """

    def get_permissions(self):
        return [IsAuthenticated(), IsActiveAccount(), IsOrganizationAdmin()]

    @extend_schema(tags=["competitions"], responses={200: CompetitionConfigSerializer})
    def get(self, request, competition_id):
        tenant = OrganizationService.get_organization_for_user(user=request.user)
        OrganizationService.assert_is_organization_admin(user=request.user, tenant=tenant)

        try:
            competition = CompetitionService.get_competition_for_tenant(
                tenant=tenant,
                competition_id=competition_id,
            )
        except CompetitionNotFound:
            return not_found_response(message="Competition not found.")

        return success_response(
            data=CompetitionConfigSerializer(competition).data,
            message="Competition configuration retrieved successfully.",
        )

    @extend_schema(
        tags=["competitions"],
        request=CompetitionConfigSerializer,
        responses={200: CompetitionConfigSerializer},
    )
    def patch(self, request, competition_id):
        tenant = OrganizationService.get_organization_for_user(user=request.user)
        OrganizationService.assert_is_organization_admin(user=request.user, tenant=tenant)

        try:
            competition = CompetitionService.get_competition_for_tenant(
                tenant=tenant,
                competition_id=competition_id,
            )
        except CompetitionNotFound:
            return not_found_response(message="Competition not found.")

        serializer = CompetitionConfigSerializer(competition, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        competition = CompetitionService.update_competition_config(
            competition=competition,
            config=serializer.validated_data.get("config", competition.config),
        )

        return success_response(
            data=CompetitionConfigSerializer(competition).data,
            message="Competition configuration updated successfully.",
        )
