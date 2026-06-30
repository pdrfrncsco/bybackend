import logging

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from accounts.permissions import IsActiveAccount
from common.responses import success_response, created_response, not_found_response, error_response
from organizations.permissions import IsOrganizationAdmin
from organizations.services import OrganizationService
from competitions.exceptions import CompetitionNotFound, DuplicateCompetition
from competitions.selectors import CompetitionSelector
from competitions.services import CompetitionService
from competitions.serializers import (
    CompetitionSerializer,
    CompetitionCreateSerializer,
    CompetitionUpdateSerializer,
)

logger = logging.getLogger(__name__)


class CompetitionListCreateView(APIView):
    """
    List or create competitions for the authenticated user's organization.
    """

    permission_classes = [IsAuthenticated, IsActiveAccount, IsOrganizationAdmin]

    @extend_schema(tags=["competitions"], responses={200: CompetitionSerializer(many=True)})
    def get(self, request):
        tenant = OrganizationService.get_organization_for_user(user=request.user)
        competitions = CompetitionSelector.list_for_tenant(tenant=tenant)
        serializer = CompetitionSerializer(competitions, many=True)
        return success_response(
            data=serializer.data,
            message="Competitions retrieved successfully.",
        )

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
    Retrieve or update a competition by ID.
    """

    permission_classes = [IsAuthenticated, IsActiveAccount, IsOrganizationAdmin]

    @extend_schema(tags=["competitions"], responses={200: CompetitionSerializer})
    def get(self, request, competition_id):
        tenant = OrganizationService.get_organization_for_user(user=request.user)
        try:
            competition = CompetitionService.get_competition_for_tenant(
                tenant=tenant,
                competition_id=competition_id,
            )
        except CompetitionNotFound:
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

        return success_response(
            data=CompetitionSerializer(competition).data,
            message="Competition updated successfully.",
        )
