"""
BOLAYETU — Partidas Selector Layer
Skills: BOLAYETU_ARCHITECTURE, BOLAYETU_BACKEND_SKILL, BOLAYETU_MULTITENANT_SKILL
"""

from django.db.models import QuerySet, Q
from common.base import BaseSelector
from .models import Match


class MatchSelector(BaseSelector):
    """
    Selector layer for retrieving Match details.
    """

    def list_matches(self, *, team_id: str = None) -> QuerySet:
        """
        List matches, scoped by tenant, optionally filtered by home/away team.
        """
        qs = self._base_qs(Match).select_related(
            'home_team',
            'away_team',
            'home_coach',
            'away_coach',
            'venue'
        )
        
        if team_id:
            qs = qs.filter(Q(home_team_id=team_id) | Q(away_team_id=team_id))
            
        return qs.order_by('-date')

    def get_match_detail(self, match_id: str) -> Match:
        """
        Retrieve details of a single match, enforcing tenant isolation.
        """
        return self._base_qs(Match).select_related(
            'home_team',
            'away_team',
            'home_coach',
            'away_coach',
            'venue',
            'referee'
        ).prefetch_related('assistant_referees').get(id=match_id)
