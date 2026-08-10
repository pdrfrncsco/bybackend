"""
PlayerCareerService

Provides methods to rebuild or compute PlayerCareer entries from existing
registrations and match events. This service is intentionally simple for Phase 2
and can be extended to integrate with Match Center event streams.
"""
from typing import Optional

from django.db import transaction

from players.models import PlayerCareer, PlayerRegistration


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

        # Aggregate registrations into career rows by club+season+competition
        regs = PlayerRegistration.objects.filter(player=player).select_related("club", "competition")
        for reg in regs:
            season = None
            # If competition/season info is available on registration, prefer it
            try:
                season = getattr(reg, "season", None) or (getattr(reg.competition, "season", None) if reg.competition else None)
            except Exception:
                season = None

            # Build or update a career row
            career, _ = PlayerCareer.objects.get_or_create(
                player=player,
                club=reg.club,
                season=season,
                competition=reg.competition,
                defaults={
                    "position": getattr(reg.player, "primary_position", None) or None,
                    "appearances": reg.matches_played or 0,
                    "goals": reg.goals or 0,
                    "assists": reg.assists or 0,
                },
            )
            # If exists, ensure aggregates are up-to-date
            career.appearances = reg.matches_played or career.appearances
            career.goals = reg.goals or career.goals
            career.assists = reg.assists or career.assists
            career.save()

        return True

    @staticmethod
    def get_career_timeline(player):
        """Return player's career entries ordered by most recent season."""
        return PlayerCareer.objects.filter(player=player).select_related("club", "competition").order_by("-season", "-appearances")
