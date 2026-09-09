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
    MAX_GOALKEEPERS = 1

    # Recognized tactical formations (def, mid, fwd)
    SUPPORTED_FORMATIONS = {
        "4-4-2": (4, 4, 2),
        "4-3-3": (4, 3, 3),
        "4-2-3-1": (4, 5, 1),
        "3-5-2": (3, 5, 2),
        "5-3-2": (5, 3, 2),
        "3-4-3": (3, 4, 3),
        "4-1-4-1": (4, 5, 1),
        "4-5-1": (4, 5, 1),
        "5-4-1": (5, 4, 1),
    }

    GK_POSITIONS = {
        "gk", "gr", "guarda-redes", "guarda_redes", "guarda redes", "golo", "goalkeeper", "porteiro"
    }
    DEF_POSITIONS = {
        "cb", "dc", "lb", "le", "rb", "ld", "lwb", "rwb", "df", "def", "defesa", "lateral", "zagueiro"
    }
    MID_POSITIONS = {
        "cm", "mc", "cdm", "mdf", "cam", "mco", "mo", "lm", "me", "rm", "md", "mf", "mid", "médio", "medio", "volante", "meio-campo"
    }
    FWD_POSITIONS = {
        "st", "pl", "cf", "ac", "fw", "fwd", "att", "avançado", "avancado", "atacante", "ponta de lança", "ponta de lanca"
    }
    FLEX_POSITIONS = {
        "lw", "rw", "ee", "ed", "lm", "rm", "me", "md"
    }

    @classmethod
    def normalize_position(cls, pos: str) -> str:
        if not pos:
            return "mf"
        clean = str(pos).strip().lower()
        if clean in cls.GK_POSITIONS or "guarda" in clean or "keeper" in clean or clean == "golo":
            return "gk"
        if clean in {"cb", "dc", "defesa central", "zagueiro"}:
            return "cb"
        if clean in {"lb", "le", "lateral esquerdo"}:
            return "lb"
        if clean in {"rb", "ld", "lateral direito"}:
            return "rb"
        if clean in {"lwb", "ala esquerdo"}:
            return "lwb"
        if clean in {"rwb", "ala direito"}:
            return "rwb"
        if clean in {"df", "def", "defesa", "lateral"}:
            return "df"
        if clean in {"cdm", "mdf", "volante", "médio defensivo", "medio defensivo", "trinco"}:
            return "cdm"
        if clean in {"cam", "mco", "mo", "médio ofensivo", "medio ofensivo"}:
            return "cam"
        if clean in {"cm", "mc", "médio centro", "medio centro", "meio-campo"}:
            return "cm"
        if clean in {"lm", "me", "médio esquerdo", "medio esquerdo"}:
            return "lm"
        if clean in {"rm", "md", "médio direito", "medio direito"}:
            return "rm"
        if clean in {"mf", "mid", "médio", "medio"}:
            return "mf"
        if clean in {"lw", "ee", "extremo esquerdo", "ponta esquerda"}:
            return "lw"
        if clean in {"rw", "ed", "extremo direito", "ponta direita"}:
            return "rw"
        if clean in {"st", "pl", "ponta de lança", "ponta de lanca", "avançado", "avancado"}:
            return "st"
        if clean in {"cf", "ac", "avançado centro", "avancado centro"}:
            return "cf"
        if clean in {"fw", "fwd", "att", "atacante"}:
            return "fw"
        return clean

    @classmethod
    def is_goalkeeper_entry(cls, entry: dict) -> bool:
        if entry.get("is_goalkeeper") is True:
            return True
        pos = cls.normalize_position(str(entry.get("position", "")))
        return pos == "gk"


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
        if match.status not in [
            Match.MatchStatus.SCHEDULED,
            Match.MatchStatus.PRE_MATCH,
            Match.MatchStatus.POSTPONED,
        ]:
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
        
        # Get all player IDs from the lineup
        player_ids = [player_entry["player_id"] for player_entry in players]
        
        # Fetch all players at once to check existence and avoid multiple queries
        players_queryset = Player.objects.filter(id__in=player_ids)
        players_by_id = {str(player.id): player for player in players_queryset}
        
        # Check if all players exist
        missing_player_ids = [player_id for player_id in player_ids if str(player_id) not in players_by_id]
        if missing_player_ids:
            raise PlayerNotFound(f"Players not found: {missing_player_ids}")
        
        # Validate lineup with player DB context
        LineupService._validate_lineup(players, formation=formation, players_by_id=players_by_id)
        
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
            raw_pos = entry.get("position", "")
            norm_pos = LineupConfig.normalize_position(raw_pos)
            is_gk = (
                entry.get("is_goalkeeper", False) is True
                or norm_pos == "gk"
                or (player and player.primary_position == Player.Position.GK)
            )
            if is_gk:
                norm_pos = "gk"
            
            lineup_entry = MatchLineup.objects.create(
                tenant=tenant,
                match=match,
                club=club,
                player=player,
                status=entry.get("status", MatchLineup.LineupStatus.SUBSTITUTE),
                position=norm_pos,
                shirt_number=entry["shirt_number"],
                is_captain=entry.get("is_captain", False),
                is_goalkeeper=is_gk,
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
    def _validate_lineup(players: List[dict], formation: str = "", players_by_id: dict = None) -> None:
        """
        Validate lineup composition and tactical formation.
        
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
        
        # Check goalkeepers: exactly 1 in starting XI
        goalkeepers = []
        for p in starters:
            p_id = str(p.get("player_id", ""))
            db_player = players_by_id.get(p_id) if players_by_id else None
            is_gk = (
                p.get("is_goalkeeper") is True
                or LineupConfig.is_goalkeeper_entry(p)
                or (db_player and db_player.primary_position == Player.Position.GK)
            )
            if is_gk:
                goalkeepers.append(p)

        if len(goalkeepers) < 1:
            raise LineupValidationError(
                "É obrigatório ter exatamente 1 guarda-redes na equipa titular."
            )
        if len(goalkeepers) > 1:
            raise LineupValidationError(
                f"Apenas 1 guarda-redes é permitido na equipa titular (foram encontrados {len(goalkeepers)})."
            )
        
        # Check tactical formation if provided
        clean_formation = (formation or "").strip()
        if clean_formation:
            if clean_formation not in LineupConfig.SUPPORTED_FORMATIONS:
                supported_list = ", ".join(LineupConfig.SUPPORTED_FORMATIONS.keys())
                raise LineupValidationError(
                    f"Formação tática inválida '{clean_formation}'. Formações suportadas: {supported_list}."
                )

            req_def, req_mid, req_fwd = LineupConfig.SUPPORTED_FORMATIONS[clean_formation]
            outfield_starters = [
                p for p in starters
                if p not in goalkeepers
            ]

            def_count = 0
            mid_count = 0
            fwd_count = 0
            flex_count = 0

            for p in outfield_starters:
                raw_pos = str(p.get("position", "")).strip().lower()
                norm_pos = LineupConfig.normalize_position(raw_pos)
                if norm_pos in LineupConfig.DEF_POSITIONS or raw_pos in LineupConfig.DEF_POSITIONS:
                    def_count += 1
                elif norm_pos in LineupConfig.FLEX_POSITIONS or raw_pos in LineupConfig.FLEX_POSITIONS:
                    flex_count += 1
                elif norm_pos in LineupConfig.MID_POSITIONS or raw_pos in LineupConfig.MID_POSITIONS:
                    mid_count += 1
                elif norm_pos in LineupConfig.FWD_POSITIONS or raw_pos in LineupConfig.FWD_POSITIONS:
                    fwd_count += 1
                else:
                    mid_count += 1

            if def_count != req_def:
                raise LineupValidationError(
                    f"A formação {clean_formation} requer {req_def} defesas, mas foram escalados {def_count} defesas."
                )

            needed_mid = max(0, req_mid - mid_count)
            needed_fwd = max(0, req_fwd - fwd_count)
            if (needed_mid + needed_fwd) != flex_count:
                raise LineupValidationError(
                    f"A formação {clean_formation} requer {req_def} defesas, {req_mid} médios e {req_fwd} avançados. "
                    f"A distribuição atual dos titulares não é compatível com esta formação."
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
