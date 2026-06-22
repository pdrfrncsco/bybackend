"""
BOLAYETU — Jogadores Selector Layer
Skills: BOLAYETU_ARCHITECTURE, BOLAYETU_BACKEND_SKILL, BOLAYETU_MULTITENANT_SKILL
"""

from django.db.models import QuerySet
from common.base import BaseSelector
from .models import Player, PlayerHistory


class PlayerSelector(BaseSelector):
    """
    Selector layer for retrieving Player and PlayerHistory details.
    """

    def list_players(self, *, club_id: str = None, search_query: str = None) -> QuerySet:
        """
        List players. If tenant context exists, scope to tenant.
        Otherwise, restrict queries to a specific club (required for cross-tenant public views).
        """
        if self.tenant:
            qs = self._base_qs(Player).select_related('club').order_by('name', 'id')
        else:
            if not club_id:
                return Player.objects.none()
            qs = Player.objects.filter(club_id=club_id).select_related('club').order_by('name', 'id')

        if search_query:
            from django.db.models import Q
            qs = qs.filter(
                Q(name__icontains=search_query) |
                Q(nickname__icontains=search_query)
            )
            
        return qs

    def get_player_detail(self, player_id: str) -> Player:
        """
        Retrieve details of a player, enforcing tenant isolation.
        """
        if self.tenant:
            return self._base_qs(Player).select_related('club').prefetch_related('history').get(id=player_id)
        return Player.objects.select_related('club').prefetch_related('history').get(id=player_id)

    def list_player_history(self) -> QuerySet:
        """
        Retrieve historical stats for players scoped to the current tenant.
        """
        self._assert_tenant()
        return (
            PlayerHistory.objects.filter(player__tenant=self.tenant)
            .select_related('player', 'club')
            .order_by('-season', 'id')
        )
