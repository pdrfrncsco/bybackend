"""
BOLAYETU — CompetitionFormatService

Handles knockout draws, bracket previews, and rounds summaries for
tournaments and cups.
"""

import random
from collections import defaultdict
from datetime import datetime
import logging

from django.db import transaction
from django.utils import timezone

from clubs.models import Club
from core.models import Tenant
from competitions.constants import CompetitionType
from competitions.models import Competition, CompetitionRegistration, Match
from competitions.services.match_service import MatchService

logger = logging.getLogger("competitions")


class CompetitionFormatService:
    @staticmethod
    def _is_knockout(competition: Competition) -> bool:
        return competition.competition_type in {CompetitionType.CUP, CompetitionType.TOURNAMENT}

    @staticmethod
    def _next_power_of_two(value: int) -> int:
        power = 1
        while power < value:
            power *= 2
        return power

    @staticmethod
    def _round_label(total_slots: int, round_number: int) -> str:
        remaining = total_slots // (2 ** (round_number - 1))
        if remaining == 2:
            return "Final"
        if remaining == 4:
            return "Semi-finals"
        if remaining == 8:
            return "Quarter-finals"
        return f"Round of {remaining}"

    @staticmethod
    def _ordered_clubs(*, tenant: Tenant, competition: Competition) -> list[Club]:
        registrations = CompetitionRegistration.objects.filter(
            tenant=tenant,
            competition=competition,
        ).select_related("club").order_by("club__name")
        return [registration.club for registration in registrations]

    @staticmethod
    def _shuffle_clubs(clubs: list[Club], seed: str | None) -> list[Club]:
        ordered = list(clubs)
        if seed is None:
            random.SystemRandom().shuffle(ordered)
            return ordered
        random.Random(seed).shuffle(ordered)
        return ordered

    @staticmethod
    @transaction.atomic
    def generate_draw(
        *,
        tenant: Tenant,
        competition: Competition,
        start_date: datetime,
        rounds_interval_days: int = 7,
        seed: str | None = None,
    ) -> list[Match]:
        if not CompetitionFormatService._is_knockout(competition):
            raise ValueError("Draw is only available for cup and tournament competitions.")

        clubs = CompetitionFormatService._ordered_clubs(tenant=tenant, competition=competition)
        if len(clubs) < 2:
            return []

        Match.objects.filter(competition=competition, tenant=tenant).delete()

        if timezone.is_naive(start_date):
            start_date = timezone.make_aware(start_date, timezone.get_current_timezone())

        total_slots = CompetitionFormatService._next_power_of_two(len(clubs))
        padded_clubs = CompetitionFormatService._shuffle_clubs(clubs, seed)
        while len(padded_clubs) < total_slots:
            padded_clubs.append(None)

        round_name = CompetitionFormatService._round_label(total_slots, 1)
        created_matches: list[Match] = []
        match_date = start_date

        for index in range(0, total_slots, 2):
            home_team = padded_clubs[index]
            away_team = padded_clubs[index + 1]
            if home_team is None or away_team is None:
                continue
            match = MatchService.create_match(
                tenant=tenant,
                competition=competition,
                home_club=home_team,
                away_club=away_team,
                match_date=match_date,
                round_number=1,
                round_name=round_name,
                phase="knockout",
                group_id=None,
                venue=home_team.city or "",
            )
            created_matches.append(match)

        logger.info(
            "Generated knockout draw for Competition: %s (tenant=%s, matches=%s)",
            competition.name,
            tenant.slug,
            len(created_matches),
        )
        return created_matches

    @staticmethod
    def build_bracket(*, tenant: Tenant, competition: Competition) -> dict:
        matches = list(
            Match.objects.filter(competition=competition, tenant=tenant)
            .select_related("home_club", "away_club")
            .order_by("phase", "group_id", "round_number", "match_date")
        )
        rounds_map: dict[tuple[str | None, str | None, int], list[Match]] = defaultdict(list)
        for match in matches:
            rounds_map[(match.phase, match.group_id, match.round_number)].append(match)

        rounds = []
        for (phase, group_id, round_number), round_matches in sorted(
            rounds_map.items(),
            key=lambda item: (
                item[0][0] or "",
                item[0][1] or "",
                item[0][2],
            ),
        ):
            first_match = round_matches[0]
            rounds.append(
                {
                    "phase": phase,
                    "group_id": group_id,
                    "round_number": round_number,
                    "round_name": first_match.round_name or CompetitionFormatService._round_label(
                        max(2, len(round_matches) * 2),
                        round_number,
                    ),
                    "matches": [
                        CompetitionFormatService._serialize_match(match) for match in round_matches
                    ],
                }
            )

        return {
            "competition_id": str(competition.id),
            "competition_type": competition.competition_type,
            "rounds": rounds,
        }

    @staticmethod
    def list_rounds(*, tenant: Tenant, competition: Competition) -> list[dict]:
        matches = Match.objects.filter(competition=competition, tenant=tenant)
        grouped: dict[tuple[str | None, str | None, int], list[Match]] = defaultdict(list)
        for match in matches:
            grouped[(match.phase, match.group_id, match.round_number)].append(match)

        rounds: list[dict] = []
        for (phase, group_id, round_number), round_matches in sorted(
            grouped.items(),
            key=lambda item: (
                item[0][0] or "",
                item[0][1] or "",
                item[0][2],
            ),
        ):
            first_match = round_matches[0]
            rounds.append(
                {
                    "phase": phase,
                    "group_id": group_id,
                    "round_number": round_number,
                    "round_name": first_match.round_name or CompetitionFormatService._round_label(
                        max(2, len(round_matches) * 2),
                        round_number,
                    ),
                    "matches_count": len(round_matches),
                    "match_ids": [str(match.id) for match in round_matches],
                }
            )
        return rounds

    @staticmethod
    def _serialize_match(match: Match) -> dict:
        return {
            "id": str(match.id),
            "competition": str(match.competition_id),
            "round_number": match.round_number,
            "round_name": match.round_name,
            "phase": match.phase,
            "group_id": match.group_id,
            "home_club": {
                "id": str(match.home_club_id),
                "name": match.home_club.name,
            },
            "away_club": {
                "id": str(match.away_club_id),
                "name": match.away_club.name,
            },
            "match_date": match.match_date.isoformat(),
            "status": match.status,
            "home_score": match.home_score,
            "away_score": match.away_score,
            "venue": match.venue,
        }
