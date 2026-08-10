from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView

from common.responses import error_response, success_response
from common.pagination import StandardPagination
from players.selectors import PlayerSelector
from players.services.player_career_service import PlayerCareerService
from players.serializers.player_career import PlayerCareerSerializer


class PlayerCareerListView(APIView):
    """GET /api/v1/players/{slug}/career/ — Return player's career timeline."""

    @extend_schema(tags=["players"], summary="Get player career timeline", responses={200: PlayerCareerSerializer(many=True)})
    def get(self, request, slug: str):
        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        queryset = PlayerCareerService.get_career_timeline(player)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = PlayerCareerSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
