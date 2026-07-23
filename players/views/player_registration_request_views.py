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
    PlayerRegistrationRequestSerializer,
)
from players.services import NoPlayerProfile, PlayerService, PlayerRegistrationConflict
from players.services.player_registration_request_service import (
    DuplicatePlayerRegistrationRequest,
    PlayerRegistrationRequestService,
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

            try:
                competition = Competition.objects.get(id=competition_id)
            except Competition.DoesNotExist:
                return error_response(message="Competition not found.", status_code=404)

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
