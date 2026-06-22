"""
BOLAYETU — Organizations Selector Layer
Skills: BOLAYETU_ARCHITECTURE, BOLAYETU_BACKEND_SKILL, BOLAYETU_MULTITENANT_SKILL
"""

import re
from django.db.models import Q, Count, Sum, Max
from django.db.models.functions import Greatest
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist

from common.base import BaseSelector
from core.models import Tenant
from clubes.models import Club, ClubHistory
from torneios.models import Tournament


class OrganizationSelector(BaseSelector):
    """
    Selector for retrieving Organization (Tenant) related data.
    """

    def get_public_detail(self, slug: str) -> Tenant:
        """
        Retrieve a public tenant by its slug.
        """
        return get_object_or_404(Tenant, slug=slug, is_public=True)

    def list_public_organizations(self, *, search_query: str = None, org_type: str = None):
        """
        List public organizations, annotated with KPIs (activeTournaments, totalClubs, last_activity).
        """
        tenants = Tenant.objects.filter(is_public=True)

        if search_query:
            tenants = tenants.filter(
                Q(name__icontains=search_query) |
                Q(location__icontains=search_query) |
                Q(country__icontains=search_query)
            )

        if org_type:
            tenants = tenants.filter(type=org_type)

        tenants = tenants.annotate(
            activeTournaments=Count(
                'tournaments',
                filter=Q(tournaments__status='active'),
                distinct=True,
            ),
            totalClubs=Count('clubs', distinct=True),
            last_activity=Greatest(
                'updated_at',
                Max('tournaments__updated_at'),
                Max('clubs__updated_at'),
            )
        )
        return tenants

    def get_organization_tournaments(self, tenant: Tenant, *, is_public: bool = True):
        """
        Retrieve tournaments for a specific tenant.
        """
        qs = Tournament.objects.filter(tenant=tenant)
        if is_public:
            qs = qs.filter(is_public=True)
        return qs.order_by('-start_date')

    def get_organization_clubs(self, tenant: Tenant):
        """
        Retrieve clubs for a specific tenant.
        """
        return Club.objects.filter(tenant=tenant).order_by('name')

    def get_organization_history(self, tenant: Tenant) -> list[dict]:
        """
        Computes the organization (tenant) champions and runners-up history.
        Extracts and parses placement data to reconstruct tournaments' history.
        """
        history = (
            ClubHistory.objects.filter(club__tenant=tenant)
            .select_related('club')
            .order_by('-season', 'id')
        )

        def parse_position(placement):
            if not placement:
                return None
            match = re.search(r'\d+', placement)
            if not match:
                return None
            try:
                return int(match.group(0))
            except ValueError:
                return None

        def is_runner_up_candidate(entry):
            placement = (entry.placement or '').lower()
            if not placement:
                return False
            if 'vice' in placement or 'finalista' in placement:
                return True
            pos = parse_position(entry.placement)
            return pos == 2

        groups = {}
        for item in history:
            key = (item.season, item.tournament_name)
            groups.setdefault(key, []).append(item)

        aggregated = []
        for (season, tournament_name), entries in groups.items():
            champion = None
            runner_up = None

            trophy_entries = [e for e in entries if e.is_trophy]
            if trophy_entries:
                trophy_entries.sort(
                    key=lambda e: (
                        parse_position(e.placement) or 99,
                        str(e.id),
                    )
                )
                champion = trophy_entries[0]
            else:
                entries_with_pos = [
                    e for e in entries if parse_position(e.placement) is not None
                ]
                if entries_with_pos:
                    entries_with_pos.sort(
                        key=lambda e: (
                            parse_position(e.placement),
                            str(e.id),
                        )
                    )
                    champion = entries_with_pos[0]

            if champion:
                remaining = [e for e in entries if e.id != champion.id]
                runner_candidates = [e for e in remaining if is_runner_up_candidate(e)]
                if runner_candidates:
                    runner_candidates.sort(
                        key=lambda e: (
                            parse_position(e.placement) or 99,
                            str(e.id),
                        )
                    )
                    runner_up = runner_candidates[0]
                else:
                    remaining_with_pos = [
                        e
                        for e in remaining
                        if parse_position(e.placement) is not None
                    ]
                    if remaining_with_pos:
                        remaining_with_pos.sort(
                            key=lambda e: (
                                parse_position(e.placement),
                                str(e.id),
                            )
                        )
                        runner_up = remaining_with_pos[0]

            tournament = None
            if tournament_name:
                tournament = (
                    Tournament.objects.filter(
                        tenant=tenant,
                        name=tournament_name,
                        season=season,
                    )
                    .order_by('-start_date')
                    .first()
                )
            if not tournament:
                fallback_qs = Tournament.objects.filter(
                    tenant=tenant,
                    season=season,
                )
                if champion:
                    fallback_qs = fallback_qs.filter(clubs=champion.club)
                elif runner_up:
                    fallback_qs = fallback_qs.filter(clubs=runner_up.club)
                tournament = fallback_qs.order_by('-start_date').first()

            if tournament:
                t_type = tournament.type
                if t_type == 'League':
                    t_format = 'league'
                elif t_type == 'Knockout':
                    t_format = 'knockout'
                elif t_type == 'Groups':
                    t_format = 'groups'
                else:
                    t_format = ''
                tournament_display_name = tournament.name
            else:
                t_format = ''
                tournament_display_name = tournament_name

            explicit_champion = tournament.champion_club if tournament and tournament.champion_club_id else None
            explicit_runner_up = tournament.runner_up_club if tournament and tournament.runner_up_club_id else None

            winner_club_obj = explicit_champion or (champion.club if champion else None)
            runner_up_club_obj = explicit_runner_up or (runner_up.club if runner_up else None)

            aggregated.append(
                {
                    'season': season,
                    'tournament_name': tournament_display_name,
                    'tournament_id': str(tournament.id) if tournament else '',
                    'tournament_format': t_format,
                    'winner_club_name': winner_club_obj.name if winner_club_obj else '',
                    'runner_up_club_name': runner_up_club_obj.name if runner_up_club_obj else '',
                    'winner_club_id': str(winner_club_obj.id) if winner_club_obj else '',
                    'runner_up_club_id': str(runner_up_club_obj.id) if runner_up_club_obj else '',
                }
            )

        aggregated.sort(
            key=lambda row: (row['season'], row['tournament_name']),
            reverse=True,
        )

        return aggregated

    def get_organization_kpis(self, tenant: Tenant) -> dict:
        """
        Retrieve and calculate KPIs for the organization.
        """
        match_stats = tenant.matches.aggregate(
            total_games=Count('id', filter=Q(status='finished')),
            live_games=Count('id', filter=Q(status='live')),
            scheduled_games=Count('id', filter=Q(status='scheduled')),
            home_goals=Sum('home_score', filter=Q(status='finished')),
            away_goals=Sum('away_score', filter=Q(status='finished')),
        )

        tenant_stats = Tenant.objects.filter(id=tenant.id).aggregate(
            total_tournaments=Count('tournaments', distinct=True),
            active_tournaments=Count('tournaments', filter=Q(tournaments__status='active'), distinct=True),
            upcoming_tournaments=Count('tournaments', filter=Q(tournaments__status='upcoming'), distinct=True),
            completed_tournaments=Count('tournaments', filter=Q(tournaments__status='completed'), distinct=True),
            total_clubs=Count('clubs', distinct=True),
            active_subscribers=Count('subscribers', distinct=True),
        )

        total_games = match_stats.get('total_games') or 0
        live_games = match_stats.get('live_games') or 0
        scheduled_games = match_stats.get('scheduled_games') or 0
        home_goals = match_stats.get('home_goals') or 0
        away_goals = match_stats.get('away_goals') or 0
        total_goals = (home_goals or 0) + (away_goals or 0)
        goals_per_game = float(total_goals) / float(total_games) if total_games > 0 else 0.0

        return {
            'total_games': total_games,
            'total_goals': total_goals,
            'goals_per_game': goals_per_game,
            'live_games': live_games,
            'scheduled_games': scheduled_games,
            'active_subscribers': tenant_stats.get('active_subscribers') or 0,
            'total_tournaments': tenant_stats.get('total_tournaments') or 0,
            'active_tournaments': tenant_stats.get('active_tournaments') or 0,
            'upcoming_tournaments': tenant_stats.get('upcoming_tournaments') or 0,
            'completed_tournaments': tenant_stats.get('completed_tournaments') or 0,
            'total_clubs': tenant_stats.get('total_clubs') or 0,
        }
