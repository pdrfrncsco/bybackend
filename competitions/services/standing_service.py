"""
BOLAYETU — StandingService

Recalculates standing positions for competitions based on match results.
"""

import logging
from collections import defaultdict
from django.db import transaction

from core.models import Tenant
from competitions.models import Competition, Standing, Match

logger = logging.getLogger("competitions")


class StandingService:
    """
    Handles recalculating standings for a competition.
    """

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

            context_matches = list(finished_matches)
            for match in context_matches:
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

            tiebreakers = StandingService._get_tiebreakers(competition)
            context_standings = StandingService._sort_standings(
                standings=context_standings,
                matches=context_matches,
                tiebreakers=tiebreakers,
            )

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

    def _get_tiebreakers(competition: Competition) -> list[str]:
        config = competition.config or {}
        tiebreakers = config.get("tiebreakers")
        if isinstance(tiebreakers, list) and tiebreakers:
            return [str(item) for item in tiebreakers]
        return ["points", "goalDifference", "goalsFor"]

    def _sort_standings(
        *,
        standings: list[Standing],
        matches: list[Match],
        tiebreakers: list[str],
    ) -> list[Standing]:
        if len(standings) <= 1 or not tiebreakers:
            return sorted(standings, key=lambda standing: standing.club.name.lower())

        primary = tiebreakers[0]
        key_map = StandingService._build_sort_key_map(
            standings=standings,
            matches=matches,
            tiebreaker=primary,
        )

        grouped: dict[tuple, list[Standing]] = defaultdict(list)
        for standing in standings:
            grouped[key_map[standing.id]].append(standing)

        sorted_keys = sorted(grouped.keys(), reverse=True)
        sorted_standings: list[Standing] = []
        for key in sorted_keys:
            bucket = grouped[key]
            if len(bucket) == 1:
                sorted_standings.extend(bucket)
            else:
                sorted_standings.extend(
                    StandingService._sort_standings(
                        standings=bucket,
                        matches=matches,
                        tiebreakers=tiebreakers[1:],
                    )
                )
        return sorted_standings

    @staticmethod
    def _build_sort_key_map(
        *,
        standings: list[Standing],
        matches: list[Match],
        tiebreaker: str,
    ) -> dict[str, tuple]:
        if tiebreaker == "headToHead":
            return StandingService._head_to_head_key_map(standings=standings, matches=matches)

        key_map: dict[str, tuple] = {}
        for standing in standings:
            if tiebreaker == "points":
                key_map[standing.id] = (standing.points,)
            elif tiebreaker == "goalDifference":
                key_map[standing.id] = (standing.goal_difference,)
            elif tiebreaker == "goalsFor":
                key_map[standing.id] = (standing.goals_for,)
            elif tiebreaker == "wins":
                key_map[standing.id] = (standing.won,)
            elif tiebreaker == "draws":
                key_map[standing.id] = (standing.drawn,)
            elif tiebreaker == "losses":
                key_map[standing.id] = (-standing.lost,)
            elif tiebreaker == "played":
                key_map[standing.id] = (-standing.played,)
            else:
                key_map[standing.id] = (standing.club.name.lower(),)
        return key_map

    @staticmethod
    def _head_to_head_key_map(
        *,
        standings: list[Standing],
        matches: list[Match],
    ) -> dict[str, tuple]:
        club_ids = {standing.club_id for standing in standings}
        h2h_stats: dict[str, dict[str, int]] = {
            standing.club_id: {"points": 0, "goal_difference": 0, "goals_for": 0}
            for standing in standings
        }

        for match in matches:
            if match.home_club_id not in club_ids or match.away_club_id not in club_ids:
                continue
            if match.home_score is None or match.away_score is None:
                continue

            home_stats = h2h_stats[match.home_club_id]
            away_stats = h2h_stats[match.away_club_id]
            home_stats["goals_for"] += match.home_score
            home_stats["goal_difference"] += match.home_score - match.away_score
            away_stats["goals_for"] += match.away_score
            away_stats["goal_difference"] += match.away_score - match.home_score

            if match.home_score > match.away_score:
                home_stats["points"] += 3
            elif match.home_score < match.away_score:
                away_stats["points"] += 3
            else:
                home_stats["points"] += 1
                away_stats["points"] += 1

        return {
            standing.id: (
                h2h_stats[standing.club_id]["points"],
                h2h_stats[standing.club_id]["goal_difference"],
                h2h_stats[standing.club_id]["goals_for"],
            )
            for standing in standings
        }

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
