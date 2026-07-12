from rest_framework.permissions import AllowAny, IsAuthenticated

from common.responses import error_response
from players.permissions import CanManagePlayerProfile


def player_write_permission(request, player):
    if request.user.is_staff:
        return None
    if not CanManagePlayerProfile.can_manage(user=request.user, player=player):
        return error_response(
            message="You do not have permission to manage this player profile.",
            status_code=403,
        )
    return None


def player_can_view_all_content(request, player) -> bool:
    if not request.user.is_authenticated:
        return False
    if request.user.is_staff:
        return True
    return CanManagePlayerProfile.can_manage(user=request.user, player=player)


def player_write_permissions():
    return [IsAuthenticated()]


def player_read_permissions():
    return [AllowAny()]
