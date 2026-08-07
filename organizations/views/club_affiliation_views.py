from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from accounts.permissions import IsActiveAccount
from common.responses import created_response, error_response, not_found_response, success_response, forbidden_response
from clubs.exceptions import DuplicateClubAffiliationRequest
from clubs.models import ClubAffiliationRequest
from clubs.serializers import (
    ClubAffiliationRequestCreateSerializer,
    ClubAffiliationRequestReviewSerializer,
    ClubAffiliationRequestSerializer,
)
from clubs.services.club_affiliation_service import ClubAffiliationService
from core.models import Tenant
from organizations.permissions import IsOrganizationAdmin
from organizations.selectors import OrganizationSelector
from organizations.services import OrganizationService


class OrganizationClubRequestCreateView(APIView):
    permission_classes = [IsAuthenticated, IsActiveAccount]

    @extend_schema(tags=["organizations"], request=ClubAffiliationRequestCreateSerializer, responses={201: ClubAffiliationRequestSerializer})
    def post(self, request, slug: str):
        tenant = OrganizationSelector.get_by_slug(slug=slug)
        if tenant is None:
            return not_found_response(message="Organization not found.")

        serializer = ClubAffiliationRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            affiliation_request = ClubAffiliationService.submit_request(
                tenant=tenant,
                submitted_by=request.user,
                **serializer.validated_data,
            )
        except DuplicateClubAffiliationRequest as exc:
            return error_response(message=str(exc), status_code=409)

        msg = "Club affiliation request created."
        if serializer.validated_data.get("is_draft"):
            msg = "Club draft saved. You can edit the provisional club before submitting." 
        else:
            msg = "Club affiliation request submitted successfully."

        return created_response(
            data=ClubAffiliationRequestSerializer(affiliation_request).data,
            message=msg,
        )


class OrganizationClubRequestSubmitView(APIView):
    """Allow the original submitter to turn a draft into a pending request."""

    permission_classes = [IsAuthenticated, IsActiveAccount]

    @extend_schema(tags=["organizations"], responses={200: ClubAffiliationRequestSerializer})
    def post(self, request, slug: str, request_id: str):
        tenant = OrganizationSelector.get_by_slug(slug=slug)
        if tenant is None:
            return not_found_response(message="Organization not found.")

        try:
            affiliation_request = ClubAffiliationRequest.objects.select_related("tenant", "submitted_by", "club").get(id=request_id, tenant=tenant)
        except ClubAffiliationRequest.DoesNotExist:
            return not_found_response(message="Club affiliation request not found.")

        # Only the original submitter can submit their draft
        if not affiliation_request.submitted_by_id or affiliation_request.submitted_by_id != request.user.id:
            return forbidden_response(message="You are not allowed to submit this draft.")

        if affiliation_request.status != ClubAffiliationRequest.Status.DRAFT:
            return error_response(message="Only drafts can be submitted.", status_code=400)

        # Transition to pending
        affiliation_request.status = ClubAffiliationRequest.Status.PENDING
        affiliation_request.save(update_fields=["status", "updated_at"])  # type: ignore[arg-type]

        # Ensure provisional club exists (should already) and persist club linkage
        ClubAffiliationService._ensure_club_for_request(request_obj=affiliation_request)
        affiliation_request.save(update_fields=["club", "updated_at"])  # type: ignore[arg-type]

        return success_response(
            data=ClubAffiliationRequestSerializer(affiliation_request).data,
            message="Club affiliation request submitted for review.",
        )


class OrganizationClubRequestsView(APIView):
    permission_classes = [IsAuthenticated, IsActiveAccount, IsOrganizationAdmin]

    @extend_schema(tags=["organizations"], responses={200: ClubAffiliationRequestSerializer(many=True)})
    def get(self, request):
        tenant = OrganizationService.get_organization_for_user(user=request.user)
        OrganizationService.assert_is_organization_admin(user=request.user, tenant=tenant)

        requests = ClubAffiliationRequest.objects.filter(tenant=tenant).select_related("submitted_by", "reviewed_by", "club")
        serializer = ClubAffiliationRequestSerializer(requests, many=True)
        return success_response(data=serializer.data, message="Club affiliation requests retrieved successfully.")


class OrganizationClubRequestReviewView(APIView):
    permission_classes = [IsAuthenticated, IsActiveAccount, IsOrganizationAdmin]

    @extend_schema(tags=["organizations"], request=ClubAffiliationRequestReviewSerializer, responses={200: ClubAffiliationRequestSerializer})
    def patch(self, request, request_id):
        tenant = OrganizationService.get_organization_for_user(user=request.user)
        OrganizationService.assert_is_organization_admin(user=request.user, tenant=tenant)

        try:
            affiliation_request = ClubAffiliationRequest.objects.select_related("tenant", "submitted_by", "reviewed_by", "club").get(id=request_id, tenant=tenant)
        except ClubAffiliationRequest.DoesNotExist:
            return not_found_response(message="Club affiliation request not found.")

        serializer = ClubAffiliationRequestReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            affiliation_request = ClubAffiliationService.review_request(
                request_obj=affiliation_request,
                reviewed_by=request.user,
                approve=serializer.validated_data["approve"],
                review_notes=serializer.validated_data.get("review_notes", ""),
            )
        except ValueError as exc:
            return error_response(message=str(exc), status_code=400)

        return success_response(
            data=ClubAffiliationRequestSerializer(affiliation_request).data,
            message="Club affiliation request reviewed successfully.",
        )
