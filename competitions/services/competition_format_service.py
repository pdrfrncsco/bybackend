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
    BRACKET_CONFIG_KEY = "knockoutBracket"

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
    def _serialize_club(club: Club, *, advanced_to_round: int | None = None) -> dict:
        payload = {
            "id": str(club.id),
            "name": club.name,
        }
        if advanced_to_round is not None:
            payload["advanced_to_round"] = advanced_to_round
        return payload

    @staticmethod
    def _load_bracket_state(competition: Competition) -> dict:
        config = competition.config or {}
        state = config.get(CompetitionFormatService.BRACKET_CONFIG_KEY)
        return state if isinstance(state, dict) else {}

    @staticmethod
    def _save_bracket_state(*, competition: Competition, state: dict) -> None:
        config = dict(competition.config or {})
        config[CompetitionFormatService.BRACKET_CONFIG_KEY] = state
        competition.config = config
        competition.save(update_fields=["config", "updated_at"])

    @staticmethod
    def _winner_from_match(match: Match) -> Club | None:
        if match.home_score is None or match.away_score is None:
            return None
        if match.home_score > match.away_score:
            return match.home_club
        if match.away_score > match.home_score:
            return match.away_club
        return None

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
        shuffled_clubs = CompetitionFormatService._shuffle_clubs(clubs, seed)
        bye_count = total_slots - len(shuffled_clubs)
        bye_clubs = shuffled_clubs[:bye_count]
        match_clubs = shuffled_clubs[bye_count:]

        round_name = CompetitionFormatService._round_label(total_slots, 1)
        created_matches: list[Match] = []
        bye_advancers: list[dict] = []
        match_date = start_date

        for advancing_club in bye_clubs:
            bye_advancers.append(
                CompetitionFormatService._serialize_club(
                    advancing_club,
                    advanced_to_round=2,
                )
            )

        for index in range(0, len(match_clubs), 2):
            home_team = match_clubs[index]
            away_team = match_clubs[index + 1]
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

        bracket_state = {
            "bracket_size": total_slots,
            "seed": seed,
            "generated_rounds": [1],
            "bye_advancers": bye_advancers,
            "rounds": {
                "1": [
                    {
                        "match_id": str(match.id),
                        "home_club_id": str(match.home_club_id),
                        "away_club_id": str(match.away_club_id),
                    }
                    for match in created_matches
                ],
            },
        }
        CompetitionFormatService._save_bracket_state(competition=competition, state=bracket_state)

        logger.info(
            "Generated knockout draw for Competition: %s (tenant=%s, matches=%s)",
            competition.name,
            tenant.slug,
            len(created_matches),
        )
        return created_matches

    @staticmethod
    @transaction.atomic
    def advance_knockout_rounds(*, tenant: Tenant, competition: Competition) -> list[Match]:
        if not CompetitionFormatService._is_knockout(competition):
            return []

        state = CompetitionFormatService._load_bracket_state(competition)
        if not state:
            return []

        created_matches: list[Match] = []
        current_round = max(state.get("generated_rounds", [1]))

        while True:
            round_matches = list(
                Match.objects.filter(
                    competition=competition,
                    tenant=tenant,
                    phase="knockout",
                    round_number=current_round,
                ).select_related("home_club", "away_club").order_by("match_date", "created_at")
            )
            if not round_matches:
                break
            if any(match.status != Match.MatchStatus.FINISHED for match in round_matches):
                break

            winners: list[Club] = []
            if current_round == 1:
                for bye_entry in state.get("bye_advancers", []):
                    club_id = bye_entry.get("id")
                    if club_id:
                        winners.append(
                            Club.objects.get(id=club_id, tenant=tenant)
                        )

            for match in round_matches:
                winner = CompetitionFormatService._winner_from_match(match)
                if winner is None:
                    return created_matches
                winners.append(winner)

            if len(winners) <= 1:
                break

            next_round = current_round + 1
            if Match.objects.filter(
                competition=competition,
                tenant=tenant,
                phase="knockout",
                round_number=next_round,
            ).exists():
                break

            next_round_name = CompetitionFormatService._round_label(
                state.get("bracket_size", len(winners) * 2),
                next_round,
            )
            next_round_date = max(match.match_date for match in round_matches)
            if timezone.is_naive(next_round_date):
                next_round_date = timezone.make_aware(next_round_date, timezone.get_current_timezone())

            next_round_matches: list[Match] = []
            for index in range(0, len(winners), 2):
                home_team = winners[index]
                away_team = winners[index + 1]
                match = MatchService.create_match(
                    tenant=tenant,
                    competition=competition,
                    home_club=home_team,
                    away_club=away_team,
                    match_date=next_round_date,
                    round_number=next_round,
                    round_name=next_round_name,
                    phase="knockout",
                    group_id=None,
                    venue=home_team.city or "",
                )
                next_round_matches.append(match)

            state.setdefault("generated_rounds", []).append(next_round)
            state.setdefault("rounds", {})[str(next_round)] = [
                {
                    "match_id": str(match.id),
                    "home_club_id": str(match.home_club_id),
                    "away_club_id": str(match.away_club_id),
                }
                for match in next_round_matches
            ]
            CompetitionFormatService._save_bracket_state(competition=competition, state=state)
            created_matches.extend(next_round_matches)
            current_round = next_round

        return created_matches

    @staticmethod
    def build_bracket(
        *,
        tenant: Tenant,
        competition: Competition,
        group_id: str | None = None,
        phase: str | None = None,
    ) -> dict:
        state = CompetitionFormatService._load_bracket_state(competition)
        queryset = Match.objects.filter(competition=competition, tenant=tenant).select_related(
            "home_club",
            "away_club",
        )
        if group_id is not None:
            queryset = queryset.filter(group_id=group_id)
        if phase is not None:
            queryset = queryset.filter(phase=phase)
        matches = list(queryset.order_by("phase", "group_id", "round_number", "match_date"))
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
                    "byes": CompetitionFormatService._bracket_byes_for_round(state, round_number),
                }
            )

        return {
            "competition_id": str(competition.id),
            "competition_type": competition.competition_type,
            "rounds": rounds,
        }

    @staticmethod
    def list_rounds(
        *,
        tenant: Tenant,
        competition: Competition,
        group_id: str | None = None,
        phase: str | None = None,
    ) -> list[dict]:
        state = CompetitionFormatService._load_bracket_state(competition)
        matches = Match.objects.filter(competition=competition, tenant=tenant)
        if group_id is not None:
            matches = matches.filter(group_id=group_id)
        if phase is not None:
            matches = matches.filter(phase=phase)
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
                    "byes": CompetitionFormatService._bracket_byes_for_round(state, round_number),
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

    @staticmethod
    def _bracket_byes_for_round(state: dict, round_number: int) -> list[dict]:
        if round_number != 1:
            return []
        byes = state.get("bye_advancers", [])
        if not isinstance(byes, list):
            return []
        return [
            {
                "club": {
                    "id": entry.get("id"),
                    "name": entry.get("name"),
                },
                "advanced_to_round": entry.get("advanced_to_round", 2),
            }
            for entry in byes
        ]
