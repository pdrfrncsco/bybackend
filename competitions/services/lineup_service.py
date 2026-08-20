"""
BOLAYETU — LineupService

Business logic for match lineups management.

Key features:
    - Submit and validate lineups (min/max players, position requirements)
    - Check player eligibility (suspensions, registrations)
    - Track lineup submission status
    - Handle formation validation
"""

from django.db import models, transaction
from django.utils import timezone
from typing import Optional, List
from datetime import date

from core.models import Tenant
from players.models import Player
from players.services import PlayerNotFound
from clubs.models import Club
from competitions.models import Match, MatchLineup, LineupSubmission
from competitions.services.fair_play_service import FairPlayService


class LineupConfig:
    """Configuration for lineup rules."""
    
    MIN_STARTERS = 11
    MAX_STARTERS = 11
    MIN_SUBSTITUTES = 3
    MAX_SUBSTITUTES = 12
    MAX_TOTAL_PLAYERS = 23
    
    # Football rules
    MIN_GOALKEEPERS = 1
    MAX_GOALKEEPERS = 2


class LineupValidationError(Exception):
    """Raised when lineup validation fails."""
    pass


class PlayerNotEligible(Exception):
    """Raised when a player is not eligible to play."""
    pass


class LineupAlreadySubmitted(Exception):
    """Raised when trying to submit a lineup that's already locked."""
    pass


class LineupService:
    """
    Handles match lineup operations.
    """

    # ─── Lineup Submission ────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def submit_lineup(
        *,
        tenant: Tenant,
        match: Match,
        club: Club,
        players: List[dict],
        formation: str = "",
        submitted_by=None,
    ) -> LineupSubmission:
        """
        Submit a complete lineup for a club in a match.
        
        Args:
            tenant: Organization
            match: Match instance
            club: Club instance
            players: List of player entries, each with:
                - player_id: Player UUID
                - status: "starter" or "substitute"
                - position: Position code (e.g., "gk", "cb", "st")
                - shirt_number: Shirt number (1-99)
                - is_captain: bool (optional)
                - is_goalkeeper: bool (optional)
                - formation_position: 1-11 (optional, for starters)
            formation: Formation string (e.g., "4-3-3")
            submitted_by: User who submitted the lineup
        
        Returns:
            LineupSubmission instance
        
        Raises:
            LineupValidationError: If validation fails
            LineupAlreadySubmitted: If lineup is locked
            PlayerNotEligible: If player is suspended
        """
        # Check if match allows lineup submission
        if match.status not in [Match.MatchStatus.SCHEDULED, Match.MatchStatus.POSTPONED]:
            raise LineupValidationError(
                f"Cannot submit lineup for match with status '{match.get_status_display()}'"
            )
        
        # Check if club is in the match
        if club.id not in (match.home_club_id, match.away_club_id):
            raise LineupValidationError("Club is not participating in this match")
        
        # Get or create LineupSubmission
        submission, created = LineupSubmission.objects.get_or_create(
            tenant=tenant,
            match=match,
            club=club,
        )
        
        # Only a new or rejected submission can start a review cycle.
        editable_statuses = {
            LineupSubmission.SubmissionStatus.PENDING,
            LineupSubmission.SubmissionStatus.REJECTED,
        }
        if submission.status not in editable_statuses:
            raise LineupAlreadySubmitted(
                f"Lineup cannot be changed from status '{submission.get_status_display()}'"
            )
        
        # Validate lineup
        LineupService._validate_lineup(players)
        
        # Get all player IDs from the lineup
        player_ids = [player_entry["player_id"] for player_entry in players]
        
        # Fetch all players at once to check existence and avoid multiple queries
        players_queryset = Player.objects.filter(id__in=player_ids)
        players_by_id = {str(player.id): player for player in players_queryset}
        
        # Check if all players exist
        missing_player_ids = [player_id for player_id in player_ids if str(player_id) not in players_by_id]
        if missing_player_ids:
            raise PlayerNotFound(f"Players not found: {missing_player_ids}")
        
        # Check player eligibility
        for player_entry in players:
            player = players_by_id[str(player_entry["player_id"])]
            is_eligible, reason = FairPlayService.is_player_eligible(
                tenant=tenant,
                player=player,
                competition=match.competition,
            )
            if not is_eligible:
                raise PlayerNotEligible(
                    f"Player {player.full_name} is not eligible: {reason}"
                )
        
        # Clear existing lineup entries
        MatchLineup.objects.filter(
            tenant=tenant,
            match=match,
            club=club,
        ).delete()
        
        # Create lineup entries
        lineup_entries = []
        for entry in players:
            player = players_by_id[str(entry["player_id"])]
            
            lineup_entry = MatchLineup.objects.create(
                tenant=tenant,
                match=match,
                club=club,
                player=player,
                status=entry.get("status", MatchLineup.LineupStatus.SUBSTITUTE),
                position=entry["position"],
                shirt_number=entry["shirt_number"],
                is_captain=entry.get("is_captain", False),
                is_goalkeeper=entry.get("is_goalkeeper", False),
                formation_position=entry.get("formation_position"),
                submitted_by=submitted_by,
            )
            lineup_entries.append(lineup_entry)
        
        # Update submission
        submission.formation = formation
        submission.submit(submitted_by)
        submission.save(update_fields=["formation"])
        
        return submission

    @staticmethod
    def _validate_lineup(players: List[dict]) -> None:
        """
        Validate lineup composition.
        
        Raises:
            LineupValidationError: If validation fails
        """
        if not players:
            raise LineupValidationError("Lineup cannot be empty")
        
        starters = [p for p in players if p.get("status") == MatchLineup.LineupStatus.STARTER]
        substitutes = [p for p in players if p.get("status") == MatchLineup.LineupStatus.SUBSTITUTE]
        
        # Check number of starters
        if len(starters) < LineupConfig.MIN_STARTERS:
            raise LineupValidationError(
                f"At least {LineupConfig.MIN_STARTERS} starters required, got {len(starters)}"
            )
        
        if len(starters) > LineupConfig.MAX_STARTERS:
            raise LineupValidationError(
                f"Maximum {LineupConfig.MAX_STARTERS} starters allowed, got {len(starters)}"
            )
        
        # Check number of substitutes
        if len(substitutes) > LineupConfig.MAX_SUBSTITUTES:
            raise LineupValidationError(
                f"Maximum {LineupConfig.MAX_SUBSTITUTES} substitutes allowed, got {len(substitutes)}"
            )
        
        # Check total players
        if len(players) > LineupConfig.MAX_TOTAL_PLAYERS:
            raise LineupValidationError(
                f"Maximum {LineupConfig.MAX_TOTAL_PLAYERS} players allowed, got {len(players)}"
            )
        
        # Check goalkeepers
        goalkeepers = [p for p in starters if p.get("is_goalkeeper", False)]
        if len(goalkeepers) < LineupConfig.MIN_GOALKEEPERS:
            raise LineupValidationError(
                f"At least {LineupConfig.MIN_GOALKEEPERS} goalkeeper required in starters"
            )
        
        # Check shirt numbers are unique
        shirt_numbers = [p["shirt_number"] for p in players]
        if len(shirt_numbers) != len(set(shirt_numbers)):
            raise LineupValidationError("Shirt numbers must be unique within the lineup")
        
        # Check players are unique
        player_ids = [p["player_id"] for p in players]
        if len(player_ids) != len(set(player_ids)):
            raise LineupValidationError("A player can only appear once in the lineup")
        
        # Check captain count
        captains = [p for p in starters if p.get("is_captain", False)]
        if len(captains) > 1:
            raise LineupValidationError("Only one captain is allowed")

    # ─── Lineup Retrieval ─────────────────────────────────────────────────────

    @staticmethod
    def get_lineup_for_club(
        *,
        tenant: Tenant,
        match: Match,
        club: Club
    ) -> dict:
        """
        Get the complete lineup for a club in a match.
        
        Returns:
            Dict with starters, substitutes, formation, and submission status
        """
        try:
            submission = LineupSubmission.objects.get(
                tenant=tenant,
                match=match,
                club=club,
            )
        except LineupSubmission.DoesNotExist:
            submission = None
        
        lineup_entries = MatchLineup.objects.filter(
            tenant=tenant,
            match=match,
            club=club,
        ).select_related("player").order_by("-status", "formation_position", "shirt_number")
        
        starters = [
            {
                "player_id": str(entry.player.id),
                "player_name": entry.player.full_name,
                "position": entry.position,
                "position_display": entry.get_position_display(),
                "shirt_number": entry.shirt_number,
                "is_captain": entry.is_captain,
                "is_goalkeeper": entry.is_goalkeeper,
                "formation_position": entry.formation_position,
            }
            for entry in lineup_entries
            if entry.status == MatchLineup.LineupStatus.STARTER
        ]
        
        substitutes = [
            {
                "player_id": str(entry.player.id),
                "player_name": entry.player.full_name,
                "position": entry.position,
                "position_display": entry.get_position_display(),
                "shirt_number": entry.shirt_number,
                "is_goalkeeper": entry.is_goalkeeper,
            }
            for entry in lineup_entries
            if entry.status == MatchLineup.LineupStatus.SUBSTITUTE
        ]
        
        return {
            "match_id": str(match.id),
            "club_id": str(club.id),
            "club_name": club.name,
            "formation": submission.formation if submission else "",
            "status": submission.status if submission else "pending",
            "submitted_at": submission.submitted_at if submission else None,
            "starters": starters,
            "substitutes": substitutes,
            "total_players": len(starters) + len(substitutes),
        }

    @staticmethod
    def get_lineups_for_match(
        *,
        tenant: Tenant,
        match: Match
    ) -> dict:
        """
        Get lineups for both clubs in a match.
        
        Returns:
            Dict with home_club and away_club lineups
        """
        home_lineup = LineupService.get_lineup_for_club(
            tenant=tenant,
            match=match,
            club=match.home_club,
        )
        
        away_lineup = LineupService.get_lineup_for_club(
            tenant=tenant,
            match=match,
            club=match.away_club,
        )
        
        return {
            "match_id": str(match.id),
            "match_str": str(match),
            "home_club": home_lineup,
            "away_club": away_lineup,
        }

    # ─── Lineup Status Management ──────────────────────────────────────────────

    @staticmethod
    def confirm_lineup(
        *,
        tenant: Tenant,
        match: Match,
        club: Club,
        confirmed_by=None
    ) -> LineupSubmission:
        """Confirm a submitted lineup."""
        try:
            submission = LineupSubmission.objects.get(
                tenant=tenant,
                match=match,
                club=club,
            )
        except LineupSubmission.DoesNotExist:
            raise LineupValidationError("Lineup has not been submitted yet")
        
        if submission.status != LineupSubmission.SubmissionStatus.SUBMITTED:
            raise LineupValidationError(
                f"Cannot confirm lineup with status '{submission.get_status_display()}'"
            )

        submission.confirm(confirmed_by)
        return submission

    @staticmethod
    @transaction.atomic
    def review_lineup_submission(
        *,
        tenant: Tenant,
        match: Match,
        club: Club,
        reviewed_by=None,
        approve: bool,
        review_notes: str = "",
    ) -> LineupSubmission:
        """Review a submitted lineup and approve or reject it."""
        try:
            submission = LineupSubmission.objects.get(
                tenant=tenant,
                match=match,
                club=club,
            )
        except LineupSubmission.DoesNotExist:
            raise LineupValidationError("Lineup has not been submitted yet")

        if submission.status != LineupSubmission.SubmissionStatus.SUBMITTED:
            raise LineupValidationError(
                f"Cannot review lineup with status '{submission.get_status_display()}'"
            )

        submission.review(reviewed_by, approve=approve, review_notes=review_notes)
        return submission

    @staticmethod
    def lock_lineup(
        *,
        tenant: Tenant,
        match: Match,
        club: Club
    ) -> LineupSubmission:
        """Lock a lineup (no further changes allowed)."""
        try:
            submission = LineupSubmission.objects.get(
                tenant=tenant,
                match=match,
                club=club,
            )
        except LineupSubmission.DoesNotExist:
            raise LineupValidationError("Lineup has not been submitted yet")
        
        if submission.status != LineupSubmission.SubmissionStatus.CONFIRMED:
            raise LineupValidationError(
                f"Cannot lock lineup with status '{submission.get_status_display()}'. "
                "The lineup must be confirmed first."
            )

        submission.lock()
        return submission

    @staticmethod
    def lock_all_lineups(
        *,
        tenant: Tenant,
        match: Match
    ) -> None:
        """Lock all lineups for a match (called when match starts)."""
        LineupSubmission.objects.filter(
            tenant=tenant,
            match=match,
            status=LineupSubmission.SubmissionStatus.CONFIRMED,
        ).update(status=LineupSubmission.SubmissionStatus.LOCKED)

    # ─── Player Updates ────────────────────────────────────────────────────────

    @staticmethod
    def update_player_minutes(
        *,
        tenant: Tenant,
        match: Match,
        club: Club,
        player: Player,
        minutes_played: int,
        substituted_in_minute: Optional[int] = None,
        substituted_out_minute: Optional[int] = None,
    ) -> MatchLineup:
        """
        Update minutes played for a player after the match.
        """
        try:
            lineup_entry = MatchLineup.objects.get(
                tenant=tenant,
                match=match,
                club=club,
                player=player,
            )
        except MatchLineup.DoesNotExist:
            raise LineupValidationError(
                f"Player {player.full_name} not found in lineup for this match"
            )
        
        lineup_entry.minutes_played = minutes_played
        lineup_entry.substituted_in_minute = substituted_in_minute
        lineup_entry.substituted_out_minute = substituted_out_minute
        lineup_entry.save(update_fields=[
            "minutes_played",
            "substituted_in_minute",
            "substituted_out_minute",
            "updated_at",
        ])
        
        return lineup_entry
