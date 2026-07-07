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
    ) -> list[Standing]:
        """
        Queries all matches for a competition, recalculates points/stats for all
        registered clubs, updates Standing records, and sorts them by position.
        """
        # Get all standings for this competition
        standings = Standing.objects.filter(competition=competition, tenant=tenant)
        
        # Reset all stats
        stats_map = {}
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

        # Query all finished matches for this competition
        finished_matches = Match.objects.filter(
            competition=competition,
            tenant=tenant,
            status=Match.MatchStatus.FINISHED,
        )

        # Process each match
        for match in finished_matches:
            h_id = match.home_club_id
            a_id = match.away_club_id
            h_score = match.home_score
            a_score = match.away_score

            if h_score is None or a_score is None:
                continue

            # Ensure both clubs have stats initialized
            if h_id not in stats_map or a_id not in stats_map:
                continue

            # Update home club stats
            stats_map[h_id]["played"] += 1
            stats_map[h_id]["goals_for"] += h_score
            stats_map[h_id]["goals_against"] += a_score

            # Update away club stats
            stats_map[a_id]["played"] += 1
            stats_map[a_id]["goals_for"] += a_score
            stats_map[a_id]["goals_against"] += h_score

            if h_score > a_score:
                stats_map[h_id]["won"] += 1
                stats_map[h_id]["points"] += 3
                stats_map[a_id]["lost"] += 1
            elif h_score < a_score:
                stats_map[a_id]["won"] += 1
                stats_map[a_id]["points"] += 3
                stats_map[h_id]["lost"] += 1
            else:
                stats_map[h_id]["drawn"] += 1
                stats_map[h_id]["points"] += 1
                stats_map[a_id]["drawn"] += 1
                stats_map[a_id]["points"] += 1

        # Write recalculated stats to Standing objects
        updated_standings = []
        for club_id, stats in stats_map.items():
            standing = stats["standing_obj"]
            standing.played = stats["played"]
            standing.won = stats["won"]
            standing.drawn = stats["drawn"]
            standing.lost = stats["lost"]
            standing.goals_for = stats["goals_for"]
            standing.goals_against = stats["goals_against"]
            standing.recalculate_difference()
            standing.points = stats["points"]
            updated_standings.append(standing)

        # Sort standings by: Points (desc), Goal Difference (desc), Goals For (desc)
        # Note: can add head-to-head records here in the future if needed.
        updated_standings.sort(
            key=lambda x: (x.points, x.goal_difference, x.goals_for),
            reverse=True
        )

        # Assign positions and save
        for idx, standing in enumerate(updated_standings, start=1):
            standing.position = idx
            standing.save()

        logger.info(
            "Standings recalculated for Competition: %s (tenant=%s)",
            competition.name, tenant.slug
        )
        return updated_standings
