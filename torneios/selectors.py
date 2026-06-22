"""
BOLAYETU — Torneios Selector Layer
Skills: BOLAYETU_ARCHITECTURE, BOLAYETU_BACKEND_SKILL, BOLAYETU_MULTITENANT_SKILL
"""

from django.db.models import QuerySet, Max
from django.db.models.functions import Greatest
from common.base import BaseSelector
from .models import Tournament, TournamentGroup


class TournamentSelector(BaseSelector):
    """
    Selector layer for retrieving Tournament and TournamentGroup details.
    """

    def list_tournaments(self) -> QuerySet:
        """
        List tournaments, scoped by tenant.
        """
        return self._base_qs(Tournament).order_by('-start_date')

    def get_tournament_detail(self, tournament_id: str) -> Tournament:
        """
        Retrieve details of a tournament, enforcing tenant isolation.
        """
        return self._base_qs(Tournament).prefetch_related('clubs', 'groups').get(id=tournament_id)

    def list_tournament_groups(self, *, tournament_id: str = None) -> QuerySet:
        """
        List tournament groups, scoped by tenant.
        """
        qs = self._base_qs(TournamentGroup).select_related('tournament')
        if tournament_id:
            qs = qs.filter(tournament_id=tournament_id)
        return qs.order_by('name')

    def list_public_tournaments(self, *, tenant_slug: str = None, status_list: list = None) -> QuerySet:
        """
        Retrieve tournaments for public-facing discovery.
        """
        qs = Tournament.objects.filter(is_public=True)
        if status_list:
            qs = qs.filter(status__in=status_list)
            
        if tenant_slug:
            qs = qs.filter(tenant__slug=tenant_slug)
            
        return qs.annotate(
            last_activity=Greatest(
                'updated_at',
                Max('matches__updated_at'),
            )
        ).order_by('status', '-start_date')
