"""
PlayerCareerService

Provides methods to rebuild or compute PlayerCareer entries from existing
registrations and match events. This service is intentionally simple for Phase 2
and can be extended to integrate with Match Center event streams.
"""
from typing import Set
from django.db import transaction

from players.models import PlayerCareer, PlayerRegistration
from players.events.types import publish_player_career_updated


class PlayerCareerService:
    @staticmethod
    @transaction.atomic
    def rebuild_career_for_player(player):
        """Rebuild PlayerCareer entries for a player from PlayerRegistration data.

        This is an idempotent operation: existing PlayerCareer rows for the
        player are removed and re-created from registrations. It is a pragmatic
        way to bootstrap the model from existing data.
        """
        # Remove existing career rows for the player
        PlayerCareer.objects.filter(player=player).delete()

        # Track seasons affected for event payload
        seasons_affected: Set[str] = set()

        # Aggregate registrations into career rows by club+season+competition
        regs = PlayerRegistration.objects.filter(player=player).select_related("club", "competition")
        for reg in regs:
            season = None
            try:
                from datetime import date
                season = (
                    getattr(reg, "season", None)
                    or (reg.competition.season if reg.competition and getattr(reg.competition, "season", None) else None)
                    or (str(reg.joined_date.year) if reg.joined_date else None)
                    or str(date.today().year)
                )
            except Exception:
                from datetime import date
                season = str(date.today().year)

            if season is not None:
                seasons_affected.add(str(season))

            # Calculate minutes and starts from MatchLineup
            from competitions.models import Match, MatchLineup
            appearances = reg.matches_played or 0
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

            if appearances > lineup_matches:
                unaccounted = appearances - lineup_matches
                minutes = lineup_minutes + (unaccounted * 80)
                starts = lineup_starts + round(unaccounted * 0.85)
            else:
                minutes = lineup_minutes
                starts = lineup_starts

            # Build or update a career row
            career, _ = PlayerCareer.objects.get_or_create(
                player=player,
                club=reg.club,
                season=season,
                competition=reg.competition,
                defaults={
                    "position": getattr(reg.player, "primary_position", None) or None,
                    "appearances": appearances,
                    "starts": starts,
                    "minutes_played": minutes,
                    "goals": reg.goals or 0,
                    "assists": reg.assists or 0,
                    "yellow_cards": reg.yellow_cards or 0,
                    "red_cards": reg.red_cards or 0,
                },
            )
            # If exists, ensure aggregates are up-to-date
            career.appearances = appearances
            career.starts = starts
            career.minutes_played = minutes
            career.goals = reg.goals or career.goals
            career.assists = reg.assists or career.assists
            career.yellow_cards = reg.yellow_cards or career.yellow_cards
            career.red_cards = reg.red_cards or career.red_cards
            career.save()

        # Publish domain event to signal career rebuild
        try:
            publish_player_career_updated(player.id, sorted(list(seasons_affected)))
        except Exception:
            # Do not fail rebuild if event publish has issues; log if logging available
            pass

        return True

    @staticmethod
    def get_career_timeline(player):
        """Return player's career entries ordered by most recent season."""
        qs = PlayerCareer.objects.filter(player=player).select_related("club", "competition").order_by("-season", "-appearances")
        if not qs.exists() and PlayerRegistration.objects.filter(player=player).exists():
            PlayerCareerService.rebuild_career_for_player(player)
            qs = PlayerCareer.objects.filter(player=player).select_related("club", "competition").order_by("-season", "-appearances")
        return qs
