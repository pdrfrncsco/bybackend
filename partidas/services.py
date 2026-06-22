"""
BOLAYETU — Partidas Service Layer
Skills: BOLAYETU_ARCHITECTURE, BOLAYETU_BACKEND_SKILL, BOLAYETU_MULTITENANT_SKILL
"""

from django.db.models import Q
from common.base import BaseService
from .models import Match
from treinadores.models import HistoricoTreinador


class MatchService(BaseService):
    """
    Service layer for mutating Match state.
    """

    @BaseService.atomic
    def create_match(self, *, data: dict, request_keys: set = None) -> Match:
        """
        Creates a new match under the current tenant context.
        Automatically resolves and assigns coaches active at the match date.
        """
        self._assert_tenant()
        
        match = Match(tenant=self.tenant)
        for field, value in data.items():
            if hasattr(match, field) and field not in ['id', 'tenant', 'created_at', 'updated_at']:
                setattr(match, field, value)
                
        match.full_clean()
        match.save()
        
        self.auto_assign_coaches(match=match, request_keys=request_keys)
        return match

    @BaseService.atomic
    def update_match(self, *, match: Match, data: dict, request_keys: set = None) -> Match:
        """
        Updates an existing match, enforcing tenant isolation.
        Automatically resolves and assigns coaches active at the match date.
        """
        self._assert_tenant()
        if match.tenant != self.tenant:
            from common.exceptions import PermissionDeniedException
            raise PermissionDeniedException("You cannot edit a match of another tenant.")

        for field, value in data.items():
            if hasattr(match, field) and field not in ['id', 'tenant', 'created_at', 'updated_at']:
                setattr(match, field, value)

        match.full_clean()
        match.save()
        
        self.auto_assign_coaches(match=match, request_keys=request_keys)
        return match

    @BaseService.atomic
    def delete_match(self, *, match: Match) -> None:
        """
        Deletes a match.
        """
        self._assert_tenant()
        if match.tenant != self.tenant:
            from common.exceptions import PermissionDeniedException
            raise PermissionDeniedException("You cannot delete a match of another tenant.")
            
        match.delete()

    @BaseService.atomic
    def auto_assign_coaches(self, *, match: Match, request_keys: set = None) -> None:
        """
        Automatically resolves and assigns the active coaches for home and away clubs on the match date.
        If a coach was explicitly provided in the request keys, it will not be overridden.
        """
        if not match.date:
            return

        skip_home = False
        skip_away = False
        if request_keys:
            skip_home = 'home_coach' in request_keys
            skip_away = 'away_coach' in request_keys

        target_date = match.date.date()

        def resolve_active_coach(club, skip_flag):
            if not club or skip_flag:
                return None
            qs = HistoricoTreinador.objects.filter(
                treinador__tenant=self.tenant,
                clube=club,
                data_inicio__lte=target_date,
            ).filter(
                Q(data_fim__isnull=True) | Q(data_fim__gte=target_date),
            ).select_related('treinador').order_by('-data_inicio', '-created_at', 'id')
            row = qs.first()
            return row.treinador if row else None

        home_coach = resolve_active_coach(match.home_team, skip_home)
        away_coach = resolve_active_coach(match.away_team, skip_away)

        fields_to_update = []

        if not skip_home:
            if home_coach and match.home_coach_id != home_coach.id:
                match.home_coach = home_coach
                fields_to_update.append('home_coach')
            elif not home_coach and match.home_coach_id is not None:
                match.home_coach = None
                fields_to_update.append('home_coach')

        if not skip_away:
            if away_coach and match.away_coach_id != away_coach.id:
                match.away_coach = away_coach
                fields_to_update.append('away_coach')
            elif not away_coach and match.away_coach_id is not None:
                match.away_coach = None
                fields_to_update.append('away_coach')

        if fields_to_update:
            fields_to_update.append('updated_at')
            match.save(update_fields=fields_to_update)
