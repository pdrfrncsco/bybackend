"""
BOLAYETU — v2 Views

API views for registering clubs, generating calendars, updating match scores,
and retrieving standings.
"""

from datetime import datetime
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from accounts.permissions import IsActiveAccount
from common.responses import success_response, created_response, not_found_response, error_response
from clubs.models import Club
from core.models import Tenant
from organizations.permissions import IsOrganizationAdmin
from organizations.services import OrganizationService
from competitions.exceptions import CompetitionNotFound
from competitions.models import Competition, Match, Standing
from competitions.selectors import CompetitionSelector, CompetitionRegistrationSelector, MatchSelector, StandingSelector
from competitions.services.competition_registration_service import CompetitionRegistrationService, ClubAlreadyRegistered
from competitions.services.match_service import MatchService, MatchNotFound
from competitions.services.standing_service import StandingService
from competitions.serializers.v2_serializers import (
    CompetitionRegistrationSerializer,
    MatchSerializer,
    StandingSerializer,
)


class CompetitionRegisterClubView(APIView):
    """
    POST: Register a club in a competition (Organization Admin only).
    """
    permission_classes = [IsAuthenticated, IsActiveAccount, IsOrganizationAdmin]

    @extend_schema(
        tags=["competitions"],
        summary="Register club in a competition",
        request=CompetitionRegistrationSerializer,
        responses={201: CompetitionRegistrationSerializer},
    )
    def post(self, request, competition_id):
        tenant = OrganizationService.get_organization_for_user(user=request.user)
        OrganizationService.assert_is_organization_admin(user=request.user, tenant=tenant)

        try:
            competition = Competition.objects.get(id=competition_id, tenant=tenant)
        except Competition.DoesNotExist:
            return not_found_response(message="Competition not found.")

        club_id = request.data.get("club")
        if not club_id:
            return error_response(message="club field is required.", status_code=400)

        try:
            club = Club.objects.get(id=club_id, tenant=tenant)
        except Club.DoesNotExist:
            return not_found_response(message="Club not found.")

        try:
            registration = CompetitionRegistrationService.register_club(
                tenant=tenant,
                competition=competition,
                club=club,
            )
        except ClubAlreadyRegistered as exc:
            return error_response(message=str(exc), status_code=409)
        except Exception as exc:
            return error_response(message=str(exc), status_code=400)

        serializer = CompetitionRegistrationSerializer(registration)
        return created_response(
            data=serializer.data,
            message="Club registered in competition successfully.",
        )


class CompetitionGenerateScheduleView(APIView):
    """
    POST: Generate weekly matches for all registered clubs (Organization Admin only).
    """
    permission_classes = [IsAuthenticated, IsActiveAccount, IsOrganizationAdmin]

    @extend_schema(
        tags=["competitions"],
        summary="Generate matches calendar schedule",
        responses={200: MatchSerializer(many=True)},
    )
    def post(self, request, competition_id):
        tenant = OrganizationService.get_organization_for_user(user=request.user)
        OrganizationService.assert_is_organization_admin(user=request.user, tenant=tenant)

        try:
            competition = Competition.objects.get(id=competition_id, tenant=tenant)
        except Competition.DoesNotExist:
            return not_found_response(message="Competition not found.")

        start_date_str = request.data.get("start_date")
        if not start_date_str:
            return error_response(message="start_date field is required.", status_code=400)

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        except ValueError:
            return error_response(message="Invalid start_date format. Use YYYY-MM-DD.", status_code=400)

        interval = int(request.data.get("rounds_interval_days", 7))
        double_round = bool(request.data.get("double_round", True))

        try:
            matches = MatchService.generate_round_robin_schedule(
                tenant=tenant,
                competition=competition,
                start_date=start_date,
                rounds_interval_days=interval,
                double_round=double_round,
            )
        except Exception as exc:
            return error_response(message=str(exc), status_code=400)

        serializer = MatchSerializer(matches, many=True)
        return success_response(
            data=serializer.data,
            message="Matches schedule generated successfully.",
        )


class CompetitionMatchListView(APIView):
    """
    GET: Retrieve match schedule/results for a competition.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["competitions"],
        summary="List matches for a competition",
        responses={200: MatchSerializer(many=True)},
    )
    def get(self, request, competition_id):
        # Resolve tenant implicitly from competition
        try:
            competition = Competition.objects.select_related("tenant").get(id=competition_id)
        except Competition.DoesNotExist:
            return not_found_response(message="Competition not found.")

        matches = MatchSelector.list_by_competition(
            tenant=competition.tenant,
            competition_id=competition_id,
        )
        serializer = MatchSerializer(matches, many=True)
        return success_response(
            data=serializer.data,
            message="Matches retrieved successfully.",
        )


class MatchScoreUpdateView(APIView):
    """
    PATCH: Update match score and recalculate standings (Organization Admin only).
    """
    permission_classes = [IsAuthenticated, IsActiveAccount, IsOrganizationAdmin]

    @extend_schema(
        tags=["competitions"],
        summary="Update match score",
        responses={200: MatchSerializer},
    )
    def patch(self, request, match_id):
        tenant = OrganizationService.get_organization_for_user(user=request.user)
        OrganizationService.assert_is_organization_admin(user=request.user, tenant=tenant)

        home_score = request.data.get("home_score")
        away_score = request.data.get("away_score")

        if home_score is None or away_score is None:
            return error_response(
                message="Both home_score and away_score are required.",
                status_code=400,
            )

        try:
            home_score = int(home_score)
            away_score = int(away_score)
        except ValueError:
            return error_response(message="Scores must be integer values.", status_code=400)

        status = request.data.get("status", Match.MatchStatus.FINISHED)

        try:
            match = MatchService.update_match_score(
                tenant=tenant,
                match_id=match_id,
                home_score=home_score,
                away_score=away_score,
                status=status,
            )
        except MatchNotFound:
            return not_found_response(message="Match not found.")
        except Exception as exc:
            return error_response(message=str(exc), status_code=400)

        serializer = MatchSerializer(match)
        return success_response(
            data=serializer.data,
            message="Match score updated and standings recalculated.",
        )


class CompetitionStandingListView(APIView):
    """
    GET: Retrieve the standings/league table for a competition.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["competitions"],
        summary="Get standings table for a competition",
        responses={200: StandingSerializer(many=True)},
    )
    def get(self, request, competition_id):
        try:
            competition = Competition.objects.select_related("tenant").get(id=competition_id)
        except Competition.DoesNotExist:
            return not_found_response(message="Competition not found.")

        standings = StandingSelector.list_by_competition(
            tenant=competition.tenant,
            competition_id=competition_id,
        )
        serializer = StandingSerializer(standings, many=True)
        return success_response(
            data=serializer.data,
            message="Standings retrieved successfully.",
        )
