"""
BOLAYETU — MatchService

Handles scheduling (round-robin generator), score updates, and match status management.
"""

import logging
from datetime import datetime, timedelta
from django.db import transaction

from core.models import Tenant
from clubs.models import Club
from competitions.models import Competition, CompetitionRegistration, Match
from competitions.services.standing_service import StandingService

logger = logging.getLogger("competitions")


class MatchNotFound(Exception):
    """Raised when a match cannot be found."""
    pass


class MatchService:
    """
    Handles match life cycle: scheduling, scoring, and status updates.
    """

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
        venue: str = "",
    ) -> Match:
        """Create a scheduled match."""
        if home_club.tenant != tenant or away_club.tenant != tenant or competition.tenant != tenant:
            raise PermissionError("All entities must belong to the same tenant.")

        match = Match.objects.create(
            competition=competition,
            tenant=tenant,
            home_club=home_club,
            away_club=away_club,
            match_date=match_date,
            round_number=round_number,
            status=Match.MatchStatus.SCHEDULED,
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
    ) -> Match:
        """
        Record final score of a match and trigger standings recalculation.
        """
        try:
            match = Match.objects.get(id=match_id, tenant=tenant)
        except Match.DoesNotExist:
            raise MatchNotFound("Match not found.")

        match.home_score = home_score
        match.away_score = away_score
        match.status = status
        match.save()

        logger.info(
            "Match %s scored: %s %s - %s %s",
            match.id, match.home_club.name, home_score, away_score, match.away_club.name
        )

        # Recalculate standings for this competition
        StandingService.recalculate_standings(tenant=tenant, competition=match.competition)

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
                    match = Match.objects.create(
                        competition=competition,
                        tenant=tenant,
                        home_club=fl_match.away_club,
                        away_club=fl_match.home_club,
                        match_date=round_date,
                        round_number=round_number,
                        status=Match.MatchStatus.SCHEDULED,
                        venue=fl_match.away_club.city or "",
                    )
                    created_matches.append(match)

        logger.info(
            "Generated %s matches for Competition: %s (tenant=%s)",
            len(created_matches), competition.name, tenant.slug
        )
        return created_matches
