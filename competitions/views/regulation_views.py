from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from accounts.permissions import IsActiveAccount
from common.responses import created_response, error_response, not_found_response, success_response
from competitions.models import Competition, CompetitionRegulation
from competitions.exceptions import DuplicateCompetitionRegulation
from competitions.selectors import CompetitionSelector
from competitions.serializers import (
    CompetitionRegulationCreateSerializer,
    CompetitionRegulationSerializer,
    CompetitionRegulationUpdateSerializer,
)
from competitions.services import CompetitionRegulationService
from organizations.permissions import IsOrganizationAdmin
from organizations.services import OrganizationService


class CompetitionRegulationListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated(), IsActiveAccount(), IsOrganizationAdmin()]

    @extend_schema(tags=["competitions"], responses={200: CompetitionRegulationSerializer(many=True)})
    def get(self, request, competition_id):
        competition = CompetitionSelector.get_by_id_public(
            competition_id=competition_id,
            tenant=getattr(request, "tenant", None),
        )
        if competition is None:
            return not_found_response(message="Competition not found.")

        regulations = competition.regulations.all().order_by("-published_at", "-created_at")
        serializer = CompetitionRegulationSerializer(regulations, many=True)
        return success_response(data=serializer.data, message="Competition regulations retrieved successfully.")

    @extend_schema(tags=["competitions"], request=CompetitionRegulationCreateSerializer, responses={201: CompetitionRegulationSerializer})
    def post(self, request, competition_id):
        tenant = OrganizationService.get_organization_for_user(user=request.user)
        OrganizationService.assert_is_organization_admin(user=request.user, tenant=tenant)

        competition = CompetitionSelector.get_by_id(tenant=tenant, competition_id=competition_id)
        if competition is None:
            return not_found_response(message="Competition not found.")

        serializer = CompetitionRegulationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            regulation = CompetitionRegulationService.create_regulation(
                tenant=tenant,
                competition=competition,
                title=serializer.validated_data["title"],
                summary=serializer.validated_data.get("summary", ""),
                version=serializer.validated_data.get("version", "1.0"),
                status=serializer.validated_data.get("status", CompetitionRegulation.Status.PUBLISHED),
                document=serializer.validated_data["document"],
                uploaded_by=request.user,
            )
        except DuplicateCompetitionRegulation as exc:
            return error_response(message=str(exc), status_code=409)

        return created_response(
            data=CompetitionRegulationSerializer(regulation).data,
            message="Competition regulation created successfully.",
        )


class CompetitionRegulationDetailView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated(), IsActiveAccount(), IsOrganizationAdmin()]

    def _get_regulation(self, *, competition_id, regulation_id, tenant=None):
        competition = CompetitionSelector.get_by_id_public(competition_id=competition_id, tenant=tenant)
        if competition is None:
            return None, None
        try:
            regulation = competition.regulations.get(id=regulation_id)
        except CompetitionRegulation.DoesNotExist:
            return competition, None
        return competition, regulation

    @extend_schema(tags=["competitions"], responses={200: CompetitionRegulationSerializer})
    def get(self, request, competition_id, regulation_id):
        competition, regulation = self._get_regulation(
            competition_id=competition_id,
            regulation_id=regulation_id,
            tenant=getattr(request, "tenant", None),
        )
        if competition is None or regulation is None:
            return not_found_response(message="Competition regulation not found.")
        return success_response(data=CompetitionRegulationSerializer(regulation).data, message="Competition regulation retrieved successfully.")

    @extend_schema(tags=["competitions"], request=CompetitionRegulationUpdateSerializer, responses={200: CompetitionRegulationSerializer})
    def patch(self, request, competition_id, regulation_id):
        tenant = OrganizationService.get_organization_for_user(user=request.user)
        OrganizationService.assert_is_organization_admin(user=request.user, tenant=tenant)

        competition, regulation = self._get_regulation(competition_id=competition_id, regulation_id=regulation_id, tenant=tenant)
        if competition is None or regulation is None:
            return not_found_response(message="Competition regulation not found.")

        serializer = CompetitionRegulationUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        regulation = CompetitionRegulationService.update_regulation(
            regulation=regulation,
            title=serializer.validated_data.get("title"),
            summary=serializer.validated_data.get("summary"),
            version=serializer.validated_data.get("version"),
            status=serializer.validated_data.get("status"),
            document=serializer.validated_data.get("document"),
            uploaded_by=request.user,
        )

        return success_response(data=CompetitionRegulationSerializer(regulation).data, message="Competition regulation updated successfully.")

    def delete(self, request, competition_id, regulation_id):
        tenant = OrganizationService.get_organization_for_user(user=request.user)
        OrganizationService.assert_is_organization_admin(user=request.user, tenant=tenant)

        competition, regulation = self._get_regulation(competition_id=competition_id, regulation_id=regulation_id, tenant=tenant)
        if competition is None or regulation is None:
            return not_found_response(message="Competition regulation not found.")

        regulation = CompetitionRegulationService.archive_regulation(regulation=regulation)
        return success_response(data=CompetitionRegulationSerializer(regulation).data, message="Competition regulation archived successfully.")
