"""
BOLAYETU — StandingService

Recalculates standing positions for competitions based on match results.
"""

import logging
from django.db import transaction

from core.models import Tenant
from competitions.models import Competition, Standing, Match

logger = logging.getLogger("competitions")


class StandingService:
    """
    Handles recalculating standings for a competition.
    """

    @staticmethod
    @transaction.atomic
    def recalculate_standings(
        *,
        tenant: Tenant,
        competition: Competition,
        group_id: str | None = None,
        phase: str | None = None,
    ) -> list[Standing]:
        """
        Recalculate standings for a competition, optionally scoped to a group
        and/or phase context.
        """
        contexts = StandingService._resolve_contexts(
            tenant=tenant,
            competition=competition,
            group_id=group_id,
            phase=phase,
        )
        config = competition.config or {}
        points_win = int(config.get("pointsWin", 3))
        points_draw = int(config.get("pointsDraw", 1))
        points_loss = int(config.get("pointsLoss", 0))

        updated_standings: list[Standing] = []
        for context_group_id, context_phase in contexts:
            standings = Standing.objects.filter(
                competition=competition,
                tenant=tenant,
            )
            if context_group_id is None:
                standings = standings.filter(group_id__isnull=True)
            else:
                standings = standings.filter(group_id=context_group_id)
            if context_phase is None:
                standings = standings.filter(phase__isnull=True)
            else:
                standings = standings.filter(phase=context_phase)

            stats_map: dict[str, dict[str, int | Standing]] = {}
            for standing in standings:
                stats_map[standing.club_id] = {
                    "played": 0,
                    "won": 0,
                    "drawn": 0,
                    "lost": 0,
                    "goals_for": 0,
                    "goals_against": 0,
                    "points": 0,
                    "standing_obj": standing,
                }

            finished_matches = Match.objects.filter(
                competition=competition,
                tenant=tenant,
                status=Match.MatchStatus.FINISHED,
            )
            if context_group_id is None:
                finished_matches = finished_matches.filter(group_id__isnull=True)
            else:
                finished_matches = finished_matches.filter(group_id=context_group_id)
            if context_phase is None:
                finished_matches = finished_matches.filter(phase__isnull=True)
            else:
                finished_matches = finished_matches.filter(phase=context_phase)

            for match in finished_matches:
                h_id = match.home_club_id
                a_id = match.away_club_id
                h_score = match.home_score
                a_score = match.away_score

                if h_score is None or a_score is None:
                    continue
                if h_id not in stats_map or a_id not in stats_map:
                    continue

                stats_map[h_id]["played"] += 1
                stats_map[h_id]["goals_for"] += h_score
                stats_map[h_id]["goals_against"] += a_score

                stats_map[a_id]["played"] += 1
                stats_map[a_id]["goals_for"] += a_score
                stats_map[a_id]["goals_against"] += h_score

                if h_score > a_score:
                    stats_map[h_id]["won"] += 1
                    stats_map[h_id]["points"] += points_win
                    stats_map[a_id]["lost"] += 1
                    stats_map[a_id]["points"] += points_loss
                elif h_score < a_score:
                    stats_map[a_id]["won"] += 1
                    stats_map[a_id]["points"] += points_win
                    stats_map[h_id]["lost"] += 1
                    stats_map[h_id]["points"] += points_loss
                else:
                    stats_map[h_id]["drawn"] += 1
                    stats_map[h_id]["points"] += points_draw
                    stats_map[a_id]["drawn"] += 1
                    stats_map[a_id]["points"] += points_draw

            context_standings: list[Standing] = []
            for stats in stats_map.values():
                standing = stats["standing_obj"]
                standing.played = int(stats["played"])
                standing.won = int(stats["won"])
                standing.drawn = int(stats["drawn"])
                standing.lost = int(stats["lost"])
                standing.goals_for = int(stats["goals_for"])
                standing.goals_against = int(stats["goals_against"])
                standing.recalculate_difference()
                standing.points = int(stats["points"])
                context_standings.append(standing)

            context_standings.sort(key=StandingService._standings_sort_key)

            for idx, standing in enumerate(context_standings, start=1):
                standing.position = idx
                standing.save()

            updated_standings.extend(context_standings)

        logger.info(
            "Standings recalculated for Competition: %s (tenant=%s)",
            competition.name,
            tenant.slug,
        )
        return updated_standings

    @staticmethod
    def _resolve_contexts(
        *,
        tenant: Tenant,
        competition: Competition,
        group_id: str | None = None,
        phase: str | None = None,
    ) -> list[tuple[str | None, str | None]]:
        if group_id is not None or phase is not None:
            return [(group_id, phase)]

        contexts = list(
            Standing.objects.filter(
                competition=competition,
                tenant=tenant,
            ).values_list("group_id", "phase").distinct()
        )
        if contexts:
            return contexts

        return list(
            Match.objects.filter(
                competition=competition,
                tenant=tenant,
            ).values_list("group_id", "phase").distinct()
        )

    @staticmethod
    def _standings_sort_key(standing: Standing) -> tuple:
        return (
            -standing.points,
            -standing.goal_difference,
            -standing.goals_for,
            -standing.won,
            -standing.drawn,
            standing.lost,
            standing.played,
            standing.club.name.lower(),
        )
