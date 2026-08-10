from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView

from common.responses import error_response, success_response
from common.pagination import StandardPagination
from players.selectors import PlayerSelector
from players.services.player_statistics_service import PlayerStatisticsService
from players.serializers.player_statistics import PlayerSeasonStatisticsSerializer


class PlayerStatisticsListView(APIView):
    """GET /api/v1/players/{slug}/statistics/ — list season stats; GET /{slug}/statistics/{season}/ for single season."""

    @extend_schema(tags=["players"], summary="Get player season statistics", responses={200: PlayerSeasonStatisticsSerializer(many=True)})
    def get(self, request, slug: str, season: str | None = None):
        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        if season:
            queryset = PlayerStatisticsService.get_statistics_for_player_and_season(player, season)
        else:
            queryset = PlayerStatisticsService.get_statistics_for_player(player)

        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = PlayerSeasonStatisticsSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(tags=["players"], summary="Rebuild player season statistics (staff only)")
    def post(self, request, slug: str):
        # Allow staff to trigger a rebuild for the player
        if not request.user or not getattr(request.user, "is_staff", False):
            return error_response(message="Forbidden.", status_code=403)

        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        PlayerStatisticsService.rebuild_for_player(player)
        return success_response(message="Player season statistics rebuilt.")
