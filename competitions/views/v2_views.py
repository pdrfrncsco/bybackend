"""
BOLAYETU — v2 Views

API views for registering clubs, generating calendars, updating match scores,
and retrieving standings.
"""

from datetime import datetime
from django.db.models import Q
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
from competitions.services.competition_format_service import CompetitionFormatService
from competitions.services.match_service import MatchService, MatchNotFound, InvalidMatchTransition
from competitions.permissions import IsMatchEventOperator
from competitions.services.standing_service import StandingService
from competitions.serializers.v2_serializers import (
    CompetitionRegistrationSerializer,
    MatchCreateSerializer,
    MatchSerializer,
    StandingSerializer,
)


def _get_query_param(request, *names: str) -> str | None:
    for name in names:
        value = request.query_params.get(name)
        if value is not None and value != "":
            return value
    return None


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

        competition = CompetitionSelector.get_by_id_public(competition_id=competition_id, tenant=tenant)
        if competition is None:
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
            if competition.competition_type == "league":
                matches = MatchService.generate_round_robin_schedule(
                    tenant=tenant,
                    competition=competition,
                    start_date=start_date,
                    rounds_interval_days=interval,
                    double_round=double_round,
                )
            else:
                matches = CompetitionFormatService.generate_draw(
                    tenant=tenant,
                    competition=competition,
                    start_date=start_date,
                    rounds_interval_days=interval,
                    seed=request.data.get("seed"),
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
    GET: Retrieve match schedule/results for a competition by ID or slug.
    POST: Create a manual match inside the competition.
    """

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated(), IsActiveAccount(), IsOrganizationAdmin()]

    @extend_schema(
        tags=["competitions"],
        summary="List matches for a competition",
        responses={200: MatchSerializer(many=True)},
    )
    def get(self, request, competition_id):
        # Resolve tenant implicitly from competition
        competition = CompetitionSelector.get_by_id_public(competition_id=competition_id)
        if competition is None:
            return not_found_response(message="Competition not found.")

        group_id = _get_query_param(request, "group_id", "groupId")
        phase = _get_query_param(request, "phase")
        matches = MatchSelector.list_by_competition(
            tenant=competition.tenant,
            competition_id=competition.id,
            group_id=group_id,
            phase=phase,
        )
        serializer = MatchSerializer(matches, many=True)
        return success_response(
            data=serializer.data,
            message="Matches retrieved successfully.",
        )

    @extend_schema(
        tags=["competitions"],
        summary="Create a manual match for a competition",
        request=MatchCreateSerializer,
        responses={201: MatchSerializer},
    )
    def post(self, request, competition_id):
        tenant = OrganizationService.get_organization_for_user(user=request.user)
        OrganizationService.assert_is_organization_admin(user=request.user, tenant=tenant)

        competition = CompetitionSelector.get_by_id_public(competition_id=competition_id, tenant=tenant)
        if competition is None:
            return not_found_response(message="Competition not found.")

        serializer = MatchCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        home_club_id = serializer.validated_data["home_club"]
        away_club_id = serializer.validated_data["away_club"]
        phase = serializer.validated_data.get("phase") or None
        group_id = serializer.validated_data.get("group_id") or None

        if competition.competition_type == "league":
            if phase or group_id:
                return error_response(
                    message="League matches do not use phase or group fields.",
                    status_code=400,
                )
            phase = None
            group_id = None
        elif competition.competition_type == "cup":
            if group_id:
                return error_response(
                    message="Cup matches do not use group fields.",
                    status_code=400,
                )
            phase = phase or "knockout"
            if phase != "knockout":
                return error_response(
                    message="Cup matches must be created in the knockout phase.",
                    status_code=400,
                )
            group_id = None
        elif competition.competition_type == "tournament":
            if phase not in {"group_stage", "knockout"}:
                return error_response(
                    message="Tournament matches require a valid phase.",
                    status_code=400,
                )
            if phase == "group_stage" and not group_id:
                return error_response(
                    message="Group stage matches require a group_id.",
                    status_code=400,
                )

        try:
            home_club = Club.objects.get(id=home_club_id, tenant=tenant)
            away_club = Club.objects.get(id=away_club_id, tenant=tenant)
        except Club.DoesNotExist:
            return not_found_response(message="Club not found.")

        try:
            match = MatchService.create_match(
                tenant=tenant,
                competition=competition,
                home_club=home_club,
                away_club=away_club,
                match_date=serializer.validated_data["match_date"],
                round_number=serializer.validated_data["round_number"],
                round_name=serializer.validated_data.get("round_name") or None,
                phase=phase,
                group_id=group_id,
                venue=serializer.validated_data.get("venue") or "",
                status=serializer.validated_data.get("status", Match.MatchStatus.SCHEDULED),
            )
        except Exception as exc:
            return error_response(message=str(exc), status_code=400)

        return created_response(
            data=MatchSerializer(match).data,
            message="Match created successfully.",
        )


class MatchDetailView(APIView):
    """
    GET: Retrieve a single match within a competition by ID.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["competitions"],
        summary="Get a match detail by competition and match id",
        responses={200: MatchSerializer},
    )
    def get(self, request, competition_id, match_id):
        competition = CompetitionSelector.get_by_id_public(competition_id=competition_id)
        if competition is None:
            return not_found_response(message="Competition not found.")

        match = MatchSelector.get_by_id(tenant=competition.tenant, match_id=match_id)
        if match is None or match.competition_id != competition.id:
            return not_found_response(message="Match not found.")

        serializer = MatchSerializer(match)
        return success_response(
            data=serializer.data,
            message="Match retrieved successfully.",
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
        current_period = request.data.get("current_period")
        current_minute = request.data.get("current_minute")

        try:
            match = MatchService.update_match_score(
                tenant=tenant,
                match_id=match_id,
                home_score=home_score,
                away_score=away_score,
                status=status,
                current_period=current_period,
                current_minute=current_minute,
            )
        except MatchNotFound:
            return not_found_response(message="Match not found.")
        except ValueError as exc:
            return error_response(message=f"Invalid match state: {exc}", status_code=400)
        except Exception as exc:
            return error_response(message=str(exc), status_code=400)

        serializer = MatchSerializer(match)
        return success_response(
            data=serializer.data,
            message="Match score updated and standings recalculated.",
        )


class MatchTransitionView(APIView):
    """PATCH: apply one validated lifecycle transition to a match."""

    permission_classes = [IsAuthenticated, IsActiveAccount, IsMatchEventOperator]

    def patch(self, request, match_id):
        tenant = OrganizationService.get_organization_for_user(user=request.user)
        status = request.data.get("status")
        if not status:
            return error_response(message="status is required.", status_code=400)
        try:
            match = MatchService.transition_match(
                tenant=tenant,
                match_id=match_id,
                status=status,
                current_period=request.data.get("current_period"),
                current_minute=request.data.get("current_minute"),
            )
        except (MatchNotFound, InvalidMatchTransition, ValueError) as exc:
            return error_response(message=str(exc), status_code=400)
        return success_response(data=MatchSerializer(match).data, message="Match transition applied.")


class CompetitionStandingListView(APIView):
    """
    GET: Retrieve the standings/league table for a competition by ID or slug.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["competitions"],
        summary="Get standings table for a competition",
        parameters=[
            OpenApiParameter("group_id", OpenApiTypes.STR, OpenApiParameter.QUERY, required=False),
            OpenApiParameter("groupId", OpenApiTypes.STR, OpenApiParameter.QUERY, required=False),
            OpenApiParameter("format", OpenApiTypes.STR, OpenApiParameter.QUERY, required=False),
            OpenApiParameter("phase", OpenApiTypes.STR, OpenApiParameter.QUERY, required=False),
        ],
        responses={200: StandingSerializer(many=True)},
    )
    def get(self, request, competition_id):
        competition = CompetitionSelector.get_by_id_public(competition_id=competition_id)
        if competition is None:
            return not_found_response(message="Competition not found.")

        group_id = _get_query_param(request, "group_id", "groupId")
        phase = _get_query_param(request, "phase")
        standings = StandingSelector.list_by_competition(
            tenant=competition.tenant,
            competition_id=competition.id,
            group_id=group_id,
            phase=phase,
        )
        serializer = StandingSerializer(standings, many=True)
        return success_response(
            data=serializer.data,
            message="Standings retrieved successfully.",
        )


class CompetitionBracketView(APIView):
    """
    GET: Retrieve the current bracket for cup/tournament competitions by ID or slug.
    """
    permission_classes = [AllowAny]

    @extend_schema(tags=["competitions"], summary="Get competition bracket")
    def get(self, request, competition_id):
        competition = CompetitionSelector.get_by_id_public(competition_id=competition_id)
        if competition is None:
            return not_found_response(message="Competition not found.")

        bracket = CompetitionFormatService.build_bracket(
            tenant=competition.tenant,
            competition=competition,
            group_id=_get_query_param(request, "group_id", "groupId"),
            phase=_get_query_param(request, "phase"),
        )
        return success_response(
            data=bracket,
            message="Bracket retrieved successfully.",
        )


class CompetitionRoundsView(APIView):
    """
    GET: Retrieve all scheduled rounds grouped by context by ID or slug.
    """
    permission_classes = [AllowAny]

    @extend_schema(tags=["competitions"], summary="Get competition rounds")
    def get(self, request, competition_id):
        competition = CompetitionSelector.get_by_id_public(competition_id=competition_id)
        if competition is None:
            return not_found_response(message="Competition not found.")

        try:
            rounds = CompetitionFormatService.list_rounds(
                tenant=competition.tenant,
                competition=competition,
                group_id=_get_query_param(request, "group_id", "groupId"),
                phase=_get_query_param(request, "phase"),
            )
        except Exception as exc:
            # Be defensive: catch validation errors coming from UUID coercion elsewhere
            from django.core.exceptions import ValidationError
            if isinstance(exc, (ValidationError, ValueError)):
                return error_response(message=str(exc), status_code=400)
            raise

        return success_response(
            data=rounds,
            message="Rounds retrieved successfully.",
        )


class CompetitionDrawView(APIView):
    """
    POST: Generate a knockout draw for cup/tournament competitions.
    """
    permission_classes = [IsAuthenticated, IsActiveAccount, IsOrganizationAdmin]

    @extend_schema(
        tags=["competitions"],
        summary="Generate competition draw",
        responses={201: MatchSerializer(many=True)},
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

        try:
            matches = CompetitionFormatService.generate_draw(
                tenant=tenant,
                competition=competition,
                start_date=start_date,
                rounds_interval_days=int(request.data.get("rounds_interval_days", 7)),
                seed=request.data.get("seed"),
            )
        except Exception as exc:
            return error_response(message=str(exc), status_code=400)

        serializer = MatchSerializer(matches, many=True)
        return created_response(
            data={
                "matches": serializer.data,
                "bracket": CompetitionFormatService.build_bracket(
                    tenant=tenant,
                    competition=competition,
                ),
            },
            message="Draw generated successfully.",
        )
