"""
BOLAYETU — Classificacoes Selector Layer
Skills: BOLAYETU_ARCHITECTURE, BOLAYETU_BACKEND_SKILL, BOLAYETU_MULTITENANT_SKILL
"""

from django.db.models import QuerySet
from common.base import BaseSelector
from .models import Standing
from torneios.models import Tournament


class StandingSelector(BaseSelector):
    """
    Selector layer for retrieving Standing records.
    """

    def list_standings(self, *, tournament_id: str = None, group_id: str = None) -> QuerySet:
        """
        List standings, enforcing tenant isolation. If tenant context is missing (public),
        it enforces filtering by tournament to resolve the appropriate tenant scope.
        """
        qs = Standing.objects.select_related('tournament', 'group', 'club')
        
        # Enforce tenant isolation
        if self.tenant:
            qs = qs.filter(tenant=self.tenant)
        elif tournament_id:
            try:
                # Public discovery resolution
                tournament = Tournament.objects.select_related('tenant').get(id=tournament_id)
                qs = qs.filter(tenant=tournament.tenant)
            except Tournament.DoesNotExist:
                return Standing.objects.none()
        else:
            return Standing.objects.none()

        if tournament_id:
            qs = qs.filter(tournament_id=tournament_id)
            
        if group_id:
            qs = qs.filter(group_id=group_id)
            
        return qs.order_by('-points', '-goals_for')
