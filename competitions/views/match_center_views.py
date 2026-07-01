"""
BOLAYETU — Match Center Views (Phase 4)

Endpoints:
  GET  /api/v1/competitions/<competition_id>/matches/<match_id>/events/  → public súmula
  POST /api/v1/competitions/<competition_id>/matches/<match_id>/events/  → add event (admin)
  DELETE /api/v1/competitions/<competition_id>/matches/<match_id>/events/<event_id>/ → remove event (admin)
  GET  /api/v1/competitions/<competition_id>/stats/  → player stats leaderboard (public)
"""

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_spectacular.utils import extend_schema

from accounts.permissions import IsActiveAccount
from clubs.models import Club
from players.models import Player
from common.responses import (
    success_response, created_response, not_found_response, error_response
)
from organizations.permissions import IsOrganizationAdmin
from organizations.services import OrganizationService
from competitions.models import Match, MatchEvent
from competitions.services.match_event_service import (
    MatchEventService, MatchEventNotFound, InvalidMatchEventData
)
from competitions.serializers.match_event_serializers import (
    MatchEventSerializer, MatchEventCreateSerializer, PlayerStatsSerializer
)


class MatchEventListCreateView(APIView):
    """
    GET  → public: list all events for a match (súmula).
    POST → org admin: add an in-game event.
    """

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated(), IsActiveAccount(), IsOrganizationAdmin()]

    @extend_schema(
        tags=["match-center"],
        summary="List match events (súmula)",
        responses={200: MatchEventSerializer(many=True)},
    )
    def get(self, request, competition_id, match_id):
        try:
            match = Match.objects.select_related("tenant").get(
                id=match_id, competition_id=competition_id
            )
        except Match.DoesNotExist:
            return not_found_response(message="Match not found.")

        events = MatchEventService.list_events_for_match(
            tenant=match.tenant, match_id=match_id
        )
        return success_response(
            data=MatchEventSerializer(events, many=True).data,
            message="Match events retrieved successfully.",
        )

    @extend_schema(
        tags=["match-center"],
        summary="Add in-game event (admin)",
        request=MatchEventCreateSerializer,
        responses={201: MatchEventSerializer},
    )
    def post(self, request, competition_id, match_id):
        tenant = OrganizationService.get_organization_for_user(user=request.user)

        try:
            match = Match.objects.get(id=match_id, competition_id=competition_id, tenant=tenant)
        except Match.DoesNotExist:
            return not_found_response(message="Match not found.")

        serializer = MatchEventCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Resolve club
        try:
            club = Club.objects.get(id=data["club"], tenant=tenant)
        except Club.DoesNotExist:
            return not_found_response(message="Club not found.")

        # Resolve optional players
        player = None
        if data.get("player"):
            try:
                player = Player.objects.get(id=data["player"])
            except Player.DoesNotExist:
                return not_found_response(message="Player not found.")

        player_off = None
        if data.get("player_off"):
            try:
                player_off = Player.objects.get(id=data["player_off"])
            except Player.DoesNotExist:
                return not_found_response(message="Player (off) not found.")

        try:
            event = MatchEventService.add_event(
                tenant=tenant,
                match=match,
                club=club,
                event_type=data["event_type"],
                minute=data["minute"],
                player=player,
                player_off=player_off,
                extra_time=data.get("extra_time", False),
                notes=data.get("notes", ""),
            )
        except InvalidMatchEventData as exc:
            return error_response(message=str(exc), status_code=400)

        return created_response(
            data=MatchEventSerializer(event).data,
            message="Event added successfully.",
        )


class MatchEventDeleteView(APIView):
    """
    DELETE → org admin: remove an event (and recalculate score if goal).
    """
    permission_classes = [IsAuthenticated, IsActiveAccount, IsOrganizationAdmin]

    @extend_schema(
        tags=["match-center"],
        summary="Remove match event (admin)",
        responses={200: None},
    )
    def delete(self, request, competition_id, match_id, event_id):
        tenant = OrganizationService.get_organization_for_user(user=request.user)
        try:
            MatchEventService.remove_event(tenant=tenant, event_id=event_id)
        except MatchEventNotFound:
            return not_found_response(message="Event not found.")
        return success_response(data=None, message="Event removed successfully.")


class CompetitionPlayerStatsView(APIView):
    """
    GET → public: player stats leaderboard for a competition.
    (goals, cards, appearances sorted by goals desc)
    """
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["match-center"],
        summary="Player stats leaderboard for competition",
        responses={200: PlayerStatsSerializer(many=True)},
    )
    def get(self, request, competition_id):
        try:
            from competitions.models import Competition
            competition = Competition.objects.select_related("tenant").get(id=competition_id)
        except Competition.DoesNotExist:
            return not_found_response(message="Competition not found.")

        stats = MatchEventService.get_player_stats_for_competition(
            tenant=competition.tenant,
            competition_id=competition_id,
        )
        return success_response(
            data=PlayerStatsSerializer(stats, many=True).data,
            message="Player stats retrieved successfully.",
        )
