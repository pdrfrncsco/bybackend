"""
BOLAYETU — Classificacoes Service Layer
Skills: BOLAYETU_ARCHITECTURE, BOLAYETU_BACKEND_SKILL, BOLAYETU_MULTITENANT_SKILL
"""

from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404

from common.base import BaseService
from .models import Standing
from torneios.models import Tournament
from partidas.models import Match


class StandingService(BaseService):
    """
    Service layer for mutating and recalculating standings.
    """

    @BaseService.atomic
    def recalculate_standings(self, *, tournament_id: str) -> list[Standing]:
        """
        Recalculates all standing metrics (played, wins, draws, losses, goals, points)
        for a tournament and its groups, based on finished matches.
        """
        self._assert_tenant()
        
        tournament = get_object_or_404(Tournament, id=tournament_id, tenant=self.tenant)
        clubs = list(tournament.clubs.all())
        
        if not clubs:
            Standing.objects.filter(tenant=self.tenant, tournament=tournament).delete()
            return []

        # Initialize statistics mapping for general standings
        stats = {}
        for club in clubs:
            stats[str(club.id)] = {
                'club': club,
                'played': 0,
                'wins': 0,
                'draws': 0,
                'losses': 0,
                'goals_for': 0,
                'goals_against': 0,
                'points': 0,
            }

        # Initialize statistics for groups if they exist
        groups = list(tournament.groups.all())
        group_stats = {}
        club_groups = {}
        for group in groups:
            group_stats[str(group.id)] = {}
            for club in group.clubs.all():
                club_id = str(club.id)
                if club_id not in group_stats[str(group.id)]:
                    group_stats[str(group.id)][club_id] = {
                        'club': club,
                        'played': 0,
                        'wins': 0,
                        'draws': 0,
                        'losses': 0,
                        'goals_for': 0,
                        'goals_against': 0,
                        'points': 0,
                    }
                if club_id not in club_groups:
                    club_groups[club_id] = set()
                club_groups[club_id].add(str(group.id))

        # Retrieve all finished matches for this tournament
        matches = Match.objects.filter(
            tenant=self.tenant,
            tournament=tournament,
            status='finished',
            home_score__isnull=False,
            away_score__isnull=False,
        ).select_related('home_team', 'away_team')

        # Accumulate metrics
        for m in matches:
            home_id = str(m.home_team_id)
            away_id = str(m.away_team_id)
            
            # Skip if clubs are not part of tournament
            if home_id not in stats or away_id not in stats:
                continue

            home = stats[home_id]
            away = stats[away_id]

            home['played'] += 1
            away['played'] += 1

            home['goals_for'] += m.home_score or 0
            home['goals_against'] += m.away_score or 0
            away['goals_for'] += m.away_score or 0
            away['goals_against'] += m.home_score or 0

            if m.home_score > m.away_score:
                home['wins'] += 1
                home['points'] += 3
                away['losses'] += 1
            elif m.home_score < m.away_score:
                away['wins'] += 1
                away['points'] += 3
                home['losses'] += 1
            else:
                home['draws'] += 1
                away['draws'] += 1
                home['points'] += 1
                away['points'] += 1

            # Update group stats
            home_groups = club_groups.get(home_id, set())
            away_groups = club_groups.get(away_id, set())
            common_groups = home_groups.intersection(away_groups)

            for group_id in common_groups:
                group_clubs = group_stats.get(group_id)
                if not group_clubs or home_id not in group_clubs or away_id not in group_clubs:
                    continue

                g_home = group_clubs[home_id]
                g_away = group_clubs[away_id]

                g_home['played'] += 1
                g_away['played'] += 1

                g_home['goals_for'] += m.home_score or 0
                g_home['goals_against'] += m.away_score or 0
                g_away['goals_for'] += m.away_score or 0
                g_away['goals_against'] += m.home_score or 0

                if m.home_score > m.away_score:
                    g_home['wins'] += 1
                    g_home['points'] += 3
                    g_away['losses'] += 1
                elif m.home_score < m.away_score:
                    g_away['wins'] += 1
                    g_away['points'] += 3
                    g_home['losses'] += 1
                else:
                    g_home['draws'] += 1
                    g_away['draws'] += 1
                    g_home['points'] += 1
                    g_away['points'] += 1

        # Delete existing standings for tournament
        Standing.objects.filter(tenant=self.tenant, tournament=tournament).delete()

        # Build list of Standing instances to bulk create
        standings = []
        
        # Build general standings
        for val in stats.values():
            standings.append(
                Standing(
                    tenant=self.tenant,
                    tournament=tournament,
                    group=None,
                    club=val['club'],
                    played=val['played'],
                    wins=val['wins'],
                    draws=val['draws'],
                    losses=val['losses'],
                    goals_for=val['goals_for'],
                    goals_against=val['goals_against'],
                    points=val['points'],
                )
            )

        # Build group standings
        for group in groups:
            group_id = str(group.id)
            group_clubs = group_stats.get(group_id, {})
            for val in group_clubs.values():
                standings.append(
                    Standing(
                        tenant=self.tenant,
                        tournament=tournament,
                        group=group,
                        club=val['club'],
                        played=val['played'],
                        wins=val['wins'],
                        draws=val['draws'],
                        losses=val['losses'],
                        goals_for=val['goals_for'],
                        goals_against=val['goals_against'],
                        points=val['points'],
                    )
                )

        created_standings = Standing.objects.bulk_create(standings)
        return created_standings
