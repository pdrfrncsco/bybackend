"""
BOLAYETU — Fair Play & Ranking Views

API views for player suspensions, eligibility checks, and rankings.
"""

from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from accounts.permissions import IsActiveAccount
from common.responses import success_response, created_response, not_found_response, error_response
from organizations.permissions import IsOrganizationAdmin
from organizations.services import OrganizationService
from players.models import Player
from clubs.models import Club
from competitions.models import Competition, PlayerSuspension, CompetitionRanking
from competitions.services.fair_play_service import FairPlayService, SuspensionAlreadyExists
from competitions.services.ranking_service import RankingService
from competitions.serializers.fair_play_serializers import (
    PlayerSuspensionSerializer,
    CreateSuspensionSerializer,
    CompetitionRankingSerializer,
    PlayerEligibilitySerializer,
    FairPlayRankingSerializer,
    TopScorerSerializer,
)


# ─── Suspensions ─────────────────────────────────────────────────────────────

class CompetitionSuspensionListView(APIView):
    """
    GET: List all active suspensions for a competition by ID or slug.
    POST: Create a manual suspension (Organization Admin only).
    """
    
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsActiveAccount(), IsOrganizationAdmin()]
        return [AllowAny()]

    @extend_schema(
        tags=["fair-play"],
        summary="List active suspensions for a competition",
        responses={200: PlayerSuspensionSerializer(many=True)},
    )
    def get(self, request, competition_id):
        try:
            competition = Competition.objects.select_related("tenant").get(
                Q(slug=competition_id) | Q(id=competition_id)
            )
        except Competition.DoesNotExist:
            return not_found_response(message="Competition not found.")
        
        suspensions = FairPlayService.get_suspended_players_for_competition(
            tenant=competition.tenant,
            competition=competition,
        )
        
        return success_response(
            data=suspensions,
            message="Suspended players retrieved successfully.",
        )

    @extend_schema(
        tags=["fair-play"],
        summary="Create a manual player suspension",
        request=CreateSuspensionSerializer,
        responses={201: PlayerSuspensionSerializer},
    )
    def post(self, request, competition_id):
        tenant = OrganizationService.get_organization_for_user(user=request.user)
        OrganizationService.assert_is_organization_admin(user=request.user, tenant=tenant)
        
        try:
            competition = Competition.objects.get(id=competition_id, tenant=tenant)
        except Competition.DoesNotExist:
            return not_found_response(message="Competition not found.")
        
        serializer = CreateSuspensionSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(message="Invalid data.", data=serializer.errors, status_code=400)
        
        try:
            player = Player.objects.get(id=serializer.validated_data["player"])
            club = Club.objects.get(id=serializer.validated_data["club"], tenant=tenant)
        except (Player.DoesNotExist, Club.DoesNotExist) as e:
            return not_found_response(message=str(e))
        
        try:
            suspension = FairPlayService.create_suspension(
                tenant=tenant,
                player=player,
                club=club,
                competition=competition,
                suspension_type=serializer.validated_data["suspension_type"],
                matches_suspended=serializer.validated_data["matches_suspended"],
                effective_from=serializer.validated_data["effective_from"],
                reason=serializer.validated_data.get("reason", ""),
                created_by=request.user,
            )
        except SuspensionAlreadyExists as e:
            return error_response(message=str(e), status_code=409)
        
        result = PlayerSuspensionSerializer(suspension).data
        return created_response(
            data=result,
            message="Suspension created successfully.",
        )


class PlayerEligibilityView(APIView):
    """
    GET: Check if a player is eligible to play in a competition by ID or slug.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["fair-play"],
        summary="Check player eligibility for a competition",
        responses={200: PlayerEligibilitySerializer},
    )
    def get(self, request, competition_id, player_id):
        try:
            competition = Competition.objects.select_related("tenant").get(
                Q(slug=competition_id) | Q(id=competition_id)
            )
        except Competition.DoesNotExist:
            return not_found_response(message="Competition not found.")
        
        try:
            player = Player.objects.get(id=player_id)
        except Player.DoesNotExist:
            return not_found_response(message="Player not found.")
        
        is_eligible, reason = FairPlayService.is_player_eligible(
            tenant=competition.tenant,
            player=player,
            competition=competition,
        )
        
        active_suspensions = FairPlayService.get_active_suspensions_for_player(
            tenant=competition.tenant,
            player=player,
            competition=competition,
        )
        
        data = {
            "player_id": str(player.id),
            "player_name": player.full_name,
            "competition_id": str(competition.id),
            "is_eligible": is_eligible,
            "reason": reason,
            "active_suspensions": PlayerSuspensionSerializer(active_suspensions, many=True).data,
        }
        
        return success_response(
            data=data,
            message="Eligibility check completed.",
        )


class PlayerSuspensionCancelView(APIView):
    """
    POST: Cancel an active or pending suspension (Organization Admin only).
    """
    permission_classes = [IsAuthenticated, IsActiveAccount, IsOrganizationAdmin]

    @extend_schema(
        tags=["fair-play"],
        summary="Cancel a player suspension",
        responses={200: PlayerSuspensionSerializer},
    )
    def post(self, request, suspension_id):
        tenant = OrganizationService.get_organization_for_user(user=request.user)
        OrganizationService.assert_is_organization_admin(user=request.user, tenant=tenant)
        
        try:
            suspension = PlayerSuspension.objects.get(id=suspension_id, tenant=tenant)
        except PlayerSuspension.DoesNotExist:
            return not_found_response(message="Suspension not found.")
        
        reason = request.data.get("reason", "")
        suspension.cancel(user=request.user, reason=reason)
        
        result = PlayerSuspensionSerializer(suspension).data
        return success_response(
            data=result,
            message="Suspension cancelled successfully.",
        )


# ─── Fair Play Rankings ──────────────────────────────────────────────────────

class CompetitionFairPlayRankingView(APIView):
    """
    GET: Get fair play ranking for a competition by ID or slug.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["rankings"],
        summary="Get fair play ranking for a competition",
        responses={200: FairPlayRankingSerializer(many=True)},
    )
    def get(self, request, competition_id):
        try:
            competition = Competition.objects.select_related("tenant").get(
                Q(slug=competition_id) | Q(id=competition_id)
            )
        except Competition.DoesNotExist:
            return not_found_response(message="Competition not found.")
        
        ranking = FairPlayService.get_fair_play_ranking_for_competition(
            tenant=competition.tenant,
            competition=competition,
        )
        
        return success_response(
            data=ranking,
            message="Fair play ranking retrieved successfully.",
        )


# ─── Rankings ────────────────────────────────────────────────────────────────

class TopScorersRankingView(APIView):
    """
    GET: Get top scorers ranking (cross-competition).
    """
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["rankings"],
        summary="Get top scorers ranking",
        parameters=[
            OpenApiParameter(
                name="season",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Season filter (e.g., '2024/2025')",
            ),
            OpenApiParameter(
                name="competition_id",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                description="Filter by specific competition",
            ),
            OpenApiParameter(
                name="limit",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Max results (default: 20)",
            ),
        ],
        responses={200: TopScorerSerializer(many=True)},
    )
    def get(self, request):
        tenant_id = request.query_params.get("tenant_id")
        season = request.query_params.get("season")
        competition_id = request.query_params.get("competition_id")
        limit = int(request.query_params.get("limit", 20))
        
        # For public access, we need tenant_id
        # For authenticated access, get tenant from user
        if request.user.is_authenticated:
            tenant = OrganizationService.get_organization_for_user(user=request.user)
        elif tenant_id:
            from core.models import Tenant
            try:
                tenant = Tenant.objects.get(id=tenant_id)
            except Tenant.DoesNotExist:
                return error_response(message="Invalid tenant_id.", status_code=400)
        else:
            return error_response(message="tenant_id is required for public access.", status_code=400)
        
        competition = None
        if competition_id:
            try:
                competition = Competition.objects.get(id=competition_id, tenant=tenant)
            except Competition.DoesNotExist:
                return not_found_response(message="Competition not found.")
        
        ranking = RankingService.get_top_scorers(
            tenant=tenant,
            season=season,
            competition=competition,
            limit=limit,
        )
        
        return success_response(
            data=ranking,
            message="Top scorers ranking retrieved successfully.",
        )


class SeasonRankingView(APIView):
    """
    GET: Get various rankings for a season.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["rankings"],
        summary="Get season rankings",
        parameters=[
            OpenApiParameter(
                name="season",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Season (e.g., '2024/2025')",
            ),
            OpenApiParameter(
                name="ranking_type",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Type: top_scorer, fair_play_club, etc.",
            ),
            OpenApiParameter(
                name="limit",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Max results (default: 20)",
            ),
        ],
        responses={200: CompetitionRankingSerializer(many=True)},
    )
    def get(self, request):
        tenant_id = request.query_params.get("tenant_id")
        season = request.query_params.get("season")
        ranking_type = request.query_params.get("ranking_type", CompetitionRanking.RankingType.TOP_SCORER)
        limit = int(request.query_params.get("limit", 20))
        
        if not season:
            return error_response(message="season parameter is required.", status_code=400)
        
        # Resolve tenant
        if request.user.is_authenticated:
            tenant = OrganizationService.get_organization_for_user(user=request.user)
        elif tenant_id:
            from core.models import Tenant
            try:
                tenant = Tenant.objects.get(id=tenant_id)
            except Tenant.DoesNotExist:
                return error_response(message="Invalid tenant_id.", status_code=400)
        else:
            return error_response(message="tenant_id is required for public access.", status_code=400)
        
        ranking = RankingService.get_ranking(
            tenant=tenant,
            ranking_type=ranking_type,
            season=season,
            limit=limit,
        )
        
        return success_response(
            data=ranking,
            message="Ranking retrieved successfully.",
        )


class RecalculateRankingsView(APIView):
    """
    POST: Trigger ranking recalculation (Organization Admin only).
    """
    permission_classes = [IsAuthenticated, IsActiveAccount, IsOrganizationAdmin]

    @extend_schema(
        tags=["rankings"],
        summary="Recalculate all rankings",
        parameters=[
            OpenApiParameter(
                name="season",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Season to recalculate (optional)",
            ),
        ],
        responses={200: OpenApiTypes.OBJECT},
    )
    def post(self, request):
        tenant = OrganizationService.get_organization_for_user(user=request.user)
        OrganizationService.assert_is_organization_admin(user=request.user, tenant=tenant)
        
        season = request.query_params.get("season")
        
        results = RankingService.recalculate_all_rankings(
            tenant=tenant,
            season=season,
        )
        
        return success_response(
            data=results,
            message="Rankings recalculated successfully.",
        )
