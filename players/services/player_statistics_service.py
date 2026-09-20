"""
PlayerSeasonStatistics service

Simple aggregator that rebuilds season statistics from PlayerRegistration records.
Intended as a bootstrap for Phase 2; can be later replaced by match-event-driven
aggregation in stats_sync_service.
"""
from collections import defaultdict
from datetime import date

from django.db import transaction

from players.models import PlayerSeasonStatistics, PlayerRegistration
from players.events.types import publish_player_season_statistics_updated


class PlayerStatisticsService:
    @staticmethod
    @transaction.atomic
    def rebuild_for_player(player):
        """Recalculate PlayerSeasonStatistics for a player from registrations.

        Strategy (pragmatic): group registrations by (club, season_key, competition)
        where season_key is derived from registration.joined_date.year if no explicit
        season is available.
        """
        # Remove existing stats
        PlayerSeasonStatistics.objects.filter(player=player).delete()

        # Track seasons affected
        seasons_affected = set()

        # Aggregate data per (club, season, competition)
        buckets = defaultdict(lambda: {
            "appearances": 0,
            "starts": 0,
            "minutes": 0,
            "goals": 0,
            "assists": 0,
            "shots": 0,
            "shots_on_target": 0,
            "yellow_cards": 0,
            "red_cards": 0,
        })

        regs = PlayerRegistration.objects.filter(player=player).select_related("club", "competition")
        for reg in regs:
            # Determine season key
            season = None
            try:
                season = (
                    getattr(reg, "season", None)
                    or (reg.competition.season if reg.competition and getattr(reg.competition, "season", None) else None)
                    or (reg.joined_date.year if reg.joined_date else None)
                    or date.today().year
                )
            except Exception:
                season = date.today().year

            if season is not None:
                seasons_affected.add(str(season))

            key = (getattr(reg.club, "id", None), season, getattr(reg.competition, "id", None))

            appearances = reg.matches_played or 0
            goals = reg.goals or 0
            assists = reg.assists or 0
            yellow_cards = reg.yellow_cards or 0
            red_cards = reg.red_cards or 0

            # Calculate minutes and starts from MatchLineup
            from competitions.models import Match, MatchLineup
            lineup_qs = MatchLineup.objects.filter(
                player=player,
                club=reg.club,
            )
            if reg.competition:
                lineup_qs = lineup_qs.filter(match__competition=reg.competition)
            lineup_qs = lineup_qs.filter(
                match__status__in=[
                    Match.MatchStatus.FINISHED,
                    Match.MatchStatus.ARCHIVED,
                    Match.MatchStatus.LIVE,
                    Match.MatchStatus.HALFTIME,
                ]
            )

            lineup_minutes = sum(l.minutes_played or 0 for l in lineup_qs)
            lineup_starts = sum(1 for l in lineup_qs if l.status == MatchLineup.LineupStatus.STARTER)
            lineup_matches = sum(
                1 for l in lineup_qs
                if l.status == MatchLineup.LineupStatus.STARTER or l.substituted_in_minute is not None or (l.minutes_played or 0) > 0
            )

            # If there are historical or imported matches in registration not represented in MatchLineup
            if appearances > lineup_matches:
                unaccounted = appearances - lineup_matches
                est_minutes = unaccounted * 80
                est_starts = round(unaccounted * 0.85)
                minutes = lineup_minutes + est_minutes
                starts = lineup_starts + est_starts
            else:
                minutes = lineup_minutes
                starts = lineup_starts

            buckets[key]["appearances"] += appearances
            buckets[key]["starts"] += starts
            buckets[key]["minutes"] += minutes
            buckets[key]["goals"] += goals
            buckets[key]["assists"] += assists
            buckets[key]["yellow_cards"] += yellow_cards
            buckets[key]["red_cards"] += red_cards

        # Persist aggregated rows
        for (club_id, season, competition_id), agg in buckets.items():
            PlayerSeasonStatistics.objects.create(
                player=player,
                season=str(season) if season is not None else None,
                club_id=club_id,
                competition_id=competition_id,
                appearances=agg["appearances"],
                goals=agg["goals"],
                assists=agg["assists"],
                yellow_cards=agg["yellow_cards"],
                red_cards=agg["red_cards"],
                starts=agg.get("starts", 0),
                minutes=agg.get("minutes", 0),
                shots=agg.get("shots", 0),
                shots_on_target=agg.get("shots_on_target", 0),
            )

        # Publish domain event
        try:
            publish_player_season_statistics_updated(player.id, sorted(list(seasons_affected)))
        except Exception:
            # don't fail rebuild on event publish problems
            pass

        return True

    @staticmethod
    def get_statistics_for_player(player):
        qs = PlayerSeasonStatistics.objects.filter(player=player).select_related("club", "competition").order_by("-season")
        if not qs.exists() and PlayerRegistration.objects.filter(player=player).exists():
            PlayerStatisticsService.rebuild_for_player(player)
            qs = PlayerSeasonStatistics.objects.filter(player=player).select_related("club", "competition").order_by("-season")
        return qs

    @staticmethod
    def get_statistics_for_player_and_season(player, season):
        qs = PlayerSeasonStatistics.objects.filter(player=player, season=str(season)).select_related("club", "competition")
        if not qs.exists() and PlayerRegistration.objects.filter(player=player).exists():
            PlayerStatisticsService.rebuild_for_player(player)
            qs = PlayerSeasonStatistics.objects.filter(player=player, season=str(season)).select_related("club", "competition")
        return qs
