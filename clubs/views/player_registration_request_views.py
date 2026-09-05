"""
Club-side views for reviewing player registration requests.
"""

from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from accounts.permissions import IsActiveAccount
from clubs.permissions import IsClubAdmin
from clubs.services import ClubService
from common.responses import error_response, not_found_response, success_response
from players.models import PlayerRegistrationRequest
from players.serializers.player_registration_request import (
    PlayerRegistrationRequestReviewSerializer,
    PlayerRegistrationRequestSerializer,
)
from players.services.player_registration_request_service import (
    PlayerRegistrationRequestService,
    RequestAlreadyReviewed,
)


class ClubMePlayerRegistrationRequestsView(APIView):
    """
    GET /api/v1/clubs/{club_id}/player-registration-requests/
    """

    permission_classes = [IsAuthenticated, IsActiveAccount, IsClubAdmin]

    @extend_schema(
        tags=["clubs"],
        responses={200: PlayerRegistrationRequestSerializer(many=True)},
    )
    def get(self, request):
        club_id = self.kwargs.get("club_id")
        club = ClubService.get_club_and_verify_admin(user=request.user, club_id=club_id) if club_id else ClubService.get_club_for_user(user=request.user)

        requests = (
            PlayerRegistrationRequest.objects.filter(club=club)
            .select_related("club", "competition", "submitted_by", "reviewed_by", "player")
            .order_by("-created_at")
        )
        serializer = PlayerRegistrationRequestSerializer(requests, many=True)
        return success_response(
            data=serializer.data,
            message="Player registration requests retrieved successfully.",
        )


class ClubMePlayerRegistrationRequestReviewView(APIView):
    """
    PATCH /api/v1/clubs/{club_id}/player-registration-requests/{request_id}/
    """

    permission_classes = [IsAuthenticated, IsActiveAccount, IsClubAdmin]

    @extend_schema(
        tags=["clubs"],
        request=PlayerRegistrationRequestReviewSerializer,
        responses={200: PlayerRegistrationRequestSerializer},
    )
    def patch(self, request, request_id, club_id=None):
        club = ClubService.get_club_and_verify_admin(user=request.user, club_id=club_id) if club_id else ClubService.get_club_for_user(user=request.user)

        try:
            registration_request = PlayerRegistrationRequest.objects.select_related(
                "club", "competition", "submitted_by", "reviewed_by", "player"
            ).get(id=request_id, club=club)
        except PlayerRegistrationRequest.DoesNotExist:
            return not_found_response(message="Player registration request not found.")

        serializer = PlayerRegistrationRequestReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            registration_request = PlayerRegistrationRequestService.review_request(
                request_obj=registration_request,
                reviewed_by=request.user,
                approve=serializer.validated_data["approve"],
                review_notes=serializer.validated_data.get("review_notes", ""),
            )
        except RequestAlreadyReviewed as exc:
            return error_response(message=str(exc), status_code=409)
        except ValueError as exc:
            return error_response(message=str(exc), status_code=400)

        output = PlayerRegistrationRequestSerializer(registration_request)
        return success_response(
            data=output.data,
            message="Player registration request reviewed successfully.",
        )
