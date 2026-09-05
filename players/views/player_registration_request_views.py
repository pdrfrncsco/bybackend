"""
Views for player-initiated club registration requests.
"""

from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from accounts.permissions import IsActiveAccount
from clubs.models import Club
from common.responses import created_response, error_response, success_response
from players.permissions import CanManagePlayerProfile
from players.serializers.player_registration_request import (
    PlayerRegistrationRequestCreateSerializer,
    PlayerRegistrationRequestDeclineSerializer,
    PlayerRegistrationRequestSerializer,
)
from players.services import NoPlayerProfile, PlayerService, PlayerRegistrationConflict
from players.services.player_registration_request_service import (
    DuplicatePlayerRegistrationRequest,
    PlayerRegistrationRequestService,
    RequestAlreadyReviewed,
)
from players.models import PlayerRegistrationRequest


class PlayerMeRegistrationRequestListCreateView(APIView):
    """
    GET  /api/v1/players/me/registration-requests/
    POST /api/v1/players/me/registration-requests/
    """

    permission_classes = [IsAuthenticated, IsActiveAccount]

    @extend_schema(
        tags=["players"],
        responses={200: PlayerRegistrationRequestSerializer(many=True)},
    )
    def get(self, request):
        try:
            player = PlayerService.get_player_for_user(request.user)
        except NoPlayerProfile:
            return error_response(message="No player profile linked to this account.", status_code=404)

        requests = (
            PlayerRegistrationRequest.objects.filter(player=player)
            .select_related("club", "competition", "submitted_by", "reviewed_by", "player")
            .order_by("-created_at")
        )
        serializer = PlayerRegistrationRequestSerializer(requests, many=True)
        return success_response(
            data=serializer.data,
            message="Player registration requests retrieved successfully.",
        )

    @extend_schema(
        tags=["players"],
        request=PlayerRegistrationRequestCreateSerializer,
        responses={201: PlayerRegistrationRequestSerializer},
    )
    def post(self, request):
        try:
            player = PlayerService.get_player_for_user(request.user)
        except NoPlayerProfile:
            return error_response(message="No player profile linked to this account.", status_code=404)

        if not CanManagePlayerProfile.can_manage(user=request.user, player=player):
            return error_response(message="You do not have permission to submit this request.", status_code=403)

        serializer = PlayerRegistrationRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        club_id = serializer.validated_data["club_id"]
        try:
            club = Club.objects.select_related("tenant").get(id=club_id)
        except Club.DoesNotExist:
            return error_response(message="Club not found.", status_code=404)

        competition = None
        competition_id = serializer.validated_data.get("competition_id")
        if competition_id:
            from competitions.models import Competition
            from competitions.models import CompetitionRegistration
            from competitions.constants import CompetitionStatus

            try:
                competition = Competition.objects.get(
                    id=competition_id,
                    tenant_id=club.tenant_id,
                    status=CompetitionStatus.ACTIVE,
                )
            except Competition.DoesNotExist:
                return error_response(message="Competition is not available for this club.", status_code=400)

            if not CompetitionRegistration.objects.filter(
                competition=competition,
                club=club,
                tenant_id=club.tenant_id,
            ).exists():
                return error_response(message="Competition is not registered for this club.", status_code=400)

        try:
            registration_request = PlayerRegistrationRequestService.submit_request(
                player=player,
                club=club,
                submitted_by=request.user,
                joined_date=serializer.validated_data["joined_date"],
                shirt_number=serializer.validated_data.get("shirt_number"),
                competition=competition,
            )
        except (DuplicatePlayerRegistrationRequest, PlayerRegistrationConflict) as exc:
            return error_response(message=str(exc), status_code=409)
        except Exception as exc:
            return error_response(message=str(exc), status_code=400)

        output = PlayerRegistrationRequestSerializer(
            PlayerRegistrationRequest.objects.select_related(
                "club", "competition", "submitted_by", "reviewed_by", "player"
            ).get(id=registration_request.id)
        )
        return created_response(
            data=output.data,
            message="Player registration request submitted successfully.",
        )


class PlayerAcceptRegistrationRequestView(APIView):
    """
    POST /api/v1/players/me/registration-requests/{id}/accept/
    """

    permission_classes = [IsAuthenticated, IsActiveAccount]

    @extend_schema(
        tags=["players"],
        responses={200: PlayerRegistrationRequestSerializer},
    )
    def post(self, request, request_id):
        try:
            player = PlayerService.get_player_for_user(request.user)
        except NoPlayerProfile:
            return error_response(message="No player profile linked to this account.", status_code=404)

        try:
            registration_request = PlayerRegistrationRequest.objects.get(
                id=request_id, player=player
            )
        except PlayerRegistrationRequest.DoesNotExist:
            return error_response(message="Registration request not found.", status_code=404)

        if not CanManagePlayerProfile.can_manage(user=request.user, player=player):
            return error_response(message="You do not have permission to accept this request.", status_code=403)

        try:
            registration_request = PlayerRegistrationRequestService.accept_request(
                request_obj=registration_request,
                accepted_by=request.user,
            )
        except RequestAlreadyReviewed as exc:
            return error_response(message=str(exc), status_code=409)
        except ValueError as exc:
            return error_response(message=str(exc), status_code=400)
        except Exception as exc:
            return error_response(message=str(exc), status_code=400)

        output = PlayerRegistrationRequestSerializer(
            PlayerRegistrationRequest.objects.select_related(
                "club", "competition", "submitted_by", "reviewed_by", "player"
            ).get(id=registration_request.id)
        )
        return success_response(
            data=output.data,
            message="Registration request accepted successfully.",
        )


class PlayerDeclineRegistrationRequestView(APIView):
    """POST /api/v1/players/me/registration-requests/{id}/decline/"""

    permission_classes = [IsAuthenticated, IsActiveAccount]

    @extend_schema(
        tags=["players"],
        request=PlayerRegistrationRequestDeclineSerializer,
        responses={200: PlayerRegistrationRequestSerializer},
    )
    def post(self, request, request_id):
        try:
            player = PlayerService.get_player_for_user(request.user)
            registration_request = PlayerRegistrationRequest.objects.get(id=request_id, player=player)
        except (NoPlayerProfile, PlayerRegistrationRequest.DoesNotExist):
            return error_response(message="Registration request not found.", status_code=404)

        if not CanManagePlayerProfile.can_manage(user=request.user, player=player):
            return error_response(message="You do not have permission to decline this request.", status_code=403)

        serializer = PlayerRegistrationRequestDeclineSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            registration_request = PlayerRegistrationRequestService.decline_invitation(
                request_obj=registration_request,
                declined_by=request.user,
                review_notes=serializer.validated_data.get("review_notes", ""),
            )
        except RequestAlreadyReviewed as exc:
            return error_response(message=str(exc), status_code=409)

        output = PlayerRegistrationRequestSerializer(registration_request)
        return success_response(data=output.data, message="Registration invitation declined successfully.")
