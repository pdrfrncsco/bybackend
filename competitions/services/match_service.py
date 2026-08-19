"""
BOLAYETU — MatchService

Handles scheduling (round-robin generator), score updates, and match status management.
"""

import logging
from datetime import datetime, timedelta
from django.db import transaction
from django.utils import timezone

from core.models import Tenant
from clubs.models import Club
from competitions.models import Competition, CompetitionRegistration, Match
from competitions.services.standing_service import StandingService
from core.events import Event, EventType, publish_event

logger = logging.getLogger("competitions")


class MatchNotFound(Exception):
    """Raised when a match cannot be found."""
    pass


class InvalidMatchTransition(Exception):
    """Raised when a match lifecycle transition is not allowed."""
    pass


class MatchService:
    """
    Handles match life cycle: scheduling, scoring, and status updates.
    """

    ALLOWED_TRANSITIONS = {
        Match.MatchStatus.SCHEDULED: {Match.MatchStatus.PRE_MATCH, Match.MatchStatus.POSTPONED, Match.MatchStatus.CANCELLED},
        Match.MatchStatus.PRE_MATCH: {Match.MatchStatus.LIVE, Match.MatchStatus.POSTPONED, Match.MatchStatus.CANCELLED},
        Match.MatchStatus.LIVE: {Match.MatchStatus.HALFTIME, Match.MatchStatus.FINISHED, Match.MatchStatus.CANCELLED},
        Match.MatchStatus.HALFTIME: {Match.MatchStatus.LIVE, Match.MatchStatus.FINISHED},
        Match.MatchStatus.FINISHED: {Match.MatchStatus.ARCHIVED},
        Match.MatchStatus.POSTPONED: {Match.MatchStatus.SCHEDULED, Match.MatchStatus.CANCELLED},
        Match.MatchStatus.WALKOVER: {Match.MatchStatus.ARCHIVED},
        Match.MatchStatus.ARCHIVED: set(),
        Match.MatchStatus.CANCELLED: set(),
    }

    @staticmethod
    @transaction.atomic
    def transition_match(*, tenant: Tenant, match_id: str, status: str,
                         current_period: str | None = None,
                         current_minute: int | None = None) -> Match:
        """Apply one explicit lifecycle transition to a locked match row."""
        try:
            match = Match.objects.select_for_update().get(id=match_id, tenant=tenant)
        except Match.DoesNotExist:
            raise MatchNotFound("Match not found.")

        MatchService.validate_match_state(status=status, current_period=current_period, current_minute=current_minute)
        if status not in MatchService.ALLOWED_TRANSITIONS.get(match.status, set()):
            raise InvalidMatchTransition(f"Cannot transition match from '{match.status}' to '{status}'.")

        match.status = status
        if current_period is not None:
            match.current_period = current_period
        if current_minute is not None:
            match.current_minute = max(0, min(int(current_minute), 130))
        match.save(update_fields=["status", "current_period", "current_minute", "updated_at"])
        publish_event(Event(
            type=EventType.MATCH_ARCHIVED if status == Match.MatchStatus.ARCHIVED else EventType.MATCH_FINISHED if status == Match.MatchStatus.FINISHED else "MatchStateChanged",
            tenant_id=str(tenant.id),
            payload={"match_id": str(match.id), "status": status},
            origin="competitions.match_service",
        ))
        return match

    @staticmethod
    def validate_match_state(
        *,
        status: str | None = None,
        current_period: str | None = None,
        current_minute: int | str | None = None,
    ) -> None:
        """Validate the canonical lifecycle values for a match update."""
        valid_statuses = {value for value, _ in Match.MatchStatus.choices} | {"archived"}
        valid_periods = {value for value, _ in Match.MatchPeriod.choices}

        if status is not None and status not in valid_statuses:
            raise ValueError(
                f"Invalid status '{status}'. Expected one of: {sorted(valid_statuses)}."
            )

        if current_period is not None and current_period not in valid_periods:
            raise ValueError(
                f"Invalid current_period '{current_period}'. Expected one of: {sorted(valid_periods)}."
            )

        if current_minute is not None:
            try:
                minute_value = int(current_minute)
            except (TypeError, ValueError) as exc:
                raise ValueError("current_minute must be an integer between 0 and 130.") from exc

            if minute_value < 0 or minute_value > 130:
                raise ValueError("current_minute must be between 0 and 130.")

    @staticmethod
    @transaction.atomic
    def create_match(
        *,
        tenant: Tenant,
        competition: Competition,
        home_club: Club,
        away_club: Club,
        match_date: datetime,
        round_number: int = 1,
        round_name: str | None = None,
        phase: str | None = None,
        group_id: str | None = None,
        venue: str = "",
        status: str = Match.MatchStatus.SCHEDULED,
    ) -> Match:
        """Create a scheduled match."""
        if home_club.tenant != tenant or away_club.tenant != tenant or competition.tenant != tenant:
            raise PermissionError("All entities must belong to the same tenant.")

        if home_club.id == away_club.id:
            raise ValueError("Home and away clubs must be different.")

        registration_filter = {
            "competition": competition,
            "tenant": tenant,
        }
        if not CompetitionRegistration.objects.filter(**registration_filter, club=home_club).exists():
            raise ValueError(f"Club {home_club.name} is not registered in this competition.")
        if not CompetitionRegistration.objects.filter(**registration_filter, club=away_club).exists():
            raise ValueError(f"Club {away_club.name} is not registered in this competition.")

        if timezone.is_naive(match_date):
            match_date = timezone.make_aware(match_date, timezone.get_current_timezone())

        match = Match.objects.create(
            competition=competition,
            tenant=tenant,
            home_club=home_club,
            away_club=away_club,
            match_date=match_date,
            round_number=round_number,
            round_name=round_name,
            phase=phase,
            group_id=group_id,
            status=status,
            venue=venue,
        )

        logger.info(
            "Match created: %s vs %s (Round %s)",
            home_club.name, away_club.name, round_number
        )
        return match

    @staticmethod
    @transaction.atomic
    def update_match_score(
        *,
        tenant: Tenant,
        match_id: str,
        home_score: int,
        away_score: int,
        status: str = Match.MatchStatus.FINISHED,
        current_period: str | None = None,
        current_minute: int | None = None,
    ) -> Match:
        """
        Record final score of a match and trigger standings recalculation.
        """
        MatchService.validate_match_state(
            status=status,
            current_period=current_period,
            current_minute=current_minute,
        )

        try:
            match = Match.objects.get(id=match_id, tenant=tenant)
        except Match.DoesNotExist:
            raise MatchNotFound("Match not found.")

        match.home_score = home_score
        match.away_score = away_score
        match.status = status

        if current_period is not None:
            match.current_period = current_period
        if current_minute is not None:
            match.current_minute = max(0, min(int(current_minute), 130))

        match.save(update_fields=["home_score", "away_score", "status", "current_period", "current_minute", "updated_at"])

        if status == Match.MatchStatus.FINISHED:
            publish_event(Event(
                type=EventType.MATCH_FINISHED,
                tenant_id=str(tenant.id),
                payload={"match_id": str(match.id), "status": status},
                origin="competitions.match_service",
            ))

        logger.info(
            "Match %s scored: %s %s - %s %s",
            match.id, match.home_club.name, home_score, away_score, match.away_club.name
        )

        # Recalculate standings for this competition
        StandingService.recalculate_standings(tenant=tenant, competition=match.competition)

        if match.competition.competition_type in {"cup", "tournament"}:
            from competitions.services.competition_format_service import CompetitionFormatService

            CompetitionFormatService.advance_knockout_rounds(
                tenant=tenant,
                competition=match.competition,
            )

        return match

    @staticmethod
    @transaction.atomic
    def generate_round_robin_schedule(
        *,
        tenant: Tenant,
        competition: Competition,
        start_date: datetime,
        rounds_interval_days: int = 7,
        double_round: bool = True,
    ) -> list[Match]:
        """
        Generates a round-robin schedule for all registered clubs in a competition.
        
        Spread matches round-by-round weekly.
        For odd number of clubs, a dummy club is added to handle "byes" (no match created).
        If double_round=True, generates home-and-away legs.
        """
        # Delete existing matches for this competition to avoid duplicates
        Match.objects.filter(competition=competition, tenant=tenant).delete()

        # Get all registered clubs
        registrations = CompetitionRegistration.objects.filter(competition=competition, tenant=tenant)
        clubs = [reg.club for reg in registrations]
        
        if len(clubs) < 2:
            return []

        # If odd number of clubs, add a dummy team for rotation
        is_odd = len(clubs) % 2 != 0
        if is_odd:
            clubs.append(None)  # None represents a "bye"

        num_teams = len(clubs)
        num_rounds = num_teams - 1
        matches_per_round = num_teams // 2

        # We will rotate teams to generate Berger table rounds
        # Berger/Round Robin rotation algorithm
        created_matches = []
        
        # Keep track of dates per round
        round_dates = [start_date + timedelta(days=r * rounds_interval_days) for r in range(num_rounds * 2 if double_round else num_rounds)]

        # Generate rounds
        for round_idx in range(num_rounds):
            round_number = round_idx + 1
            round_date = round_dates[round_idx]
            if timezone.is_naive(round_date):
                round_date = timezone.make_aware(round_date, timezone.get_current_timezone())

            for match_idx in range(matches_per_round):
                home_idx = (round_idx + match_idx) % (num_teams - 1)
                away_idx = (num_teams - 1 - match_idx + round_idx) % (num_teams - 1)

                # Fixed last team at position N-1
                if match_idx == 0:
                    away_idx = num_teams - 1

                home_team = clubs[home_idx]
                away_team = clubs[away_idx]

                # Alternate home/away for the fixed team to keep it balanced
                if match_idx == 0 and round_idx % 2 == 0:
                    home_team, away_team = away_team, home_team

                # Skip matches with dummy team (bye week)
                if home_team is None or away_team is None:
                    continue

                match = Match.objects.create(
                    competition=competition,
                    tenant=tenant,
                    home_club=home_team,
                    away_club=away_team,
                    match_date=round_date,
                    round_number=round_number,
                    round_name=f"Round {round_number}",
                    status=Match.MatchStatus.SCHEDULED,
                    venue=home_team.city or "",
                )
                created_matches.append(match)

        # Generate second leg (away matches reversed)
        if double_round:
            for round_idx in range(num_rounds):
                round_number = num_rounds + round_idx + 1
                round_date = round_dates[num_rounds + round_idx]

                # Match matches from first leg but with home/away reversed
                first_leg_round = round_idx + 1
                first_leg_matches = [m for m in created_matches if m.round_number == first_leg_round]

                for fl_match in first_leg_matches:
                    if timezone.is_naive(round_date):
                        round_date = timezone.make_aware(round_date, timezone.get_current_timezone())
                    match = Match.objects.create(
                        competition=competition,
                        tenant=tenant,
                        home_club=fl_match.away_club,
                        away_club=fl_match.home_club,
                        match_date=round_date,
                        round_number=round_number,
                        round_name=f"Round {round_number}",
                        status=Match.MatchStatus.SCHEDULED,
                        venue=fl_match.away_club.city or "",
                    )
                    created_matches.append(match)

        logger.info(
            "Generated %s matches for Competition: %s (tenant=%s)",
            len(created_matches), competition.name, tenant.slug
        )
        return created_matches
