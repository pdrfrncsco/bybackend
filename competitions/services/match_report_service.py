"""
BOLAYETU — MatchReportService

Business logic for match reports, goals, and match statistics.

Key features:
    - Record and manage match reports
    - Track goals and goal scorers
    - Manage match statistics (possession, shots, passes, etc)
    - Update player performance stats after match
    - Handle match result finalization
"""

from django.db import transaction
from django.utils import timezone
from typing import Optional, List, Tuple
from datetime import datetime

from core.models import Tenant
from players.models import Player
from clubs.models import Club
from competitions.models import Match, Goal, MatchReport, MatchStats, MatchLineup


class MatchReportError(Exception):
    """Raised when match report operation fails."""
    pass


class GoalRecordingError(Exception):
    """Raised when goal recording fails."""
    pass


class MatchReportService:
    """
    Handles match report operations and statistics management.
    """

    # ─── Report Management ─────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def create_report(
        *,
        tenant: Tenant,
        match: Match,
        home_score: int,
        away_score: int,
        match_duration: int = 90,
        created_by=None,
    ) -> MatchReport:
        """
        Create or update a match report with final score.

        Args:
            tenant: Organization
            match: Match instance
            home_score: Home team goals
            away_score: Away team goals
            match_duration: Match duration in minutes (default 90)
            created_by: User creating the report

        Returns:
            MatchReport instance

        Raises:
            MatchReportError: If operation fails
        """
        if home_score < 0 or away_score < 0:
            raise MatchReportError("Goal counts cannot be negative")

        if match_duration < 0 or match_duration > 180:
            raise MatchReportError("Match duration must be between 0 and 180 minutes")

        try:
            report, created = MatchReport.objects.get_or_create(
                match=match,
                defaults={
                    'home_score': home_score,
                    'away_score': away_score,
                    'match_duration': match_duration,
                }
            )

            if not created:
                # Update existing report
                report.home_score = home_score
                report.away_score = away_score
                report.match_duration = match_duration
                report.save()

            return report

        except Exception as e:
            raise MatchReportError(f"Failed to create report: {str(e)}")

    @staticmethod
    def get_report(*, tenant: Tenant, match: Match) -> Optional[MatchReport]:
        """Get match report for a match."""
        try:
            return MatchReport.objects.get(match=match)
        except MatchReport.DoesNotExist:
            return None

    @staticmethod
    def finalize_report(
        *,
        tenant: Tenant,
        match: Match,
        finalized_by=None
    ) -> MatchReport:
        """Finalize match report and lock lineups."""
        try:
            report = MatchReport.objects.get(match=match)
        except MatchReport.DoesNotExist:
            raise MatchReportError("Match report not found")

        if report.status == MatchReport.ReportStatus.FINALIZED:
            raise MatchReportError("Report is already finalized")

        report.finalize(finalized_by)
        return report

    # ─── Goal Management ──────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def record_goal(
        *,
        tenant: Tenant,
        match: Match,
        player: Player,
        club: Club,
        minute: int,
        goal_type: str = "normal",
        assist_player: Optional[Player] = None,
    ) -> Goal:
        """
        Record a goal in a match.

        Args:
            tenant: Organization
            match: Match instance
            player: Player who scored
            club: Player's club
            minute: Minute of the goal (1-180)
            goal_type: Type of goal ('normal', 'penalty', 'own_goal')
            assist_player: Player who assisted (optional)

        Returns:
            Goal instance

        Raises:
            GoalRecordingError: If goal recording fails
        """
        # Validate inputs
        if minute < 1 or minute > 180:
            raise GoalRecordingError("Goal minute must be between 1 and 180")

        if goal_type not in ["normal", "penalty", "own_goal"]:
            raise GoalRecordingError(f"Invalid goal type: {goal_type}")

        # Verify player registration / club
        from players.models import PlayerRegistration
        is_registered = PlayerRegistration.objects.filter(
            player=player,
            club=club,
            status__in=[PlayerRegistration.RegistrationStatus.REGISTERED, PlayerRegistration.RegistrationStatus.LOANED]
        ).exists()
        if not is_registered and hasattr(player, 'club_id') and player.club_id != club.id:
            raise GoalRecordingError(
                f"Player {player.full_name} does not belong to {club.name}"
            )

        # Verify club is in the match
        if club.id not in (match.home_club_id, match.away_club_id):
            raise GoalRecordingError(f"{club.name} is not in this match")

        try:
            goal = Goal.objects.create(
                match=match,
                player=player,
                club=club,
                minute=minute,
                goal_type=goal_type,
                assist_player=assist_player,
            )

            return goal

        except Exception as e:
            raise GoalRecordingError(f"Failed to record goal: {str(e)}")

    @staticmethod
    def get_match_goals(
        *,
        tenant: Tenant,
        match: Match,
        club: Optional[Club] = None,
    ) -> List[Goal]:
        """
        Get goals from a match.

        Args:
            tenant: Organization
            match: Match instance
            club: Filter goals by club (optional)

        Returns:
            List of Goal instances
        """
        queryset = Goal.objects.filter(match=match).select_related(
            'player', 'club', 'assist_player'
        ).order_by('minute')

        if club:
            queryset = queryset.filter(club=club)

        return list(queryset)

    @staticmethod
    def delete_goal(*, tenant: Tenant, goal: Goal) -> None:
        """Delete a goal record."""
        goal.delete()

    # ─── Statistics Management ────────────────────────────────────────────

    @staticmethod
    def update_team_stats(
        *,
        tenant: Tenant,
        match: Match,
        club: Club,
        possession: Optional[int] = None,
        shots_on_goal: Optional[int] = None,
        shots_off_goal: Optional[int] = None,
        passes: Optional[int] = None,
        passes_accuracy: Optional[int] = None,
        fouls: Optional[int] = None,
        yellow_cards: Optional[int] = None,
        red_cards: Optional[int] = None,
        corner_kicks: Optional[int] = None,
    ) -> MatchStats:
        """
        Update team statistics for a match.

        Args:
            tenant: Organization
            match: Match instance
            club: Club instance
            possession: Ball possession percentage (0-100)
            shots_on_goal: Shots on goal
            shots_off_goal: Shots off goal
            passes: Total passes
            passes_accuracy: Pass accuracy percentage (0-100)
            fouls: Number of fouls committed
            yellow_cards: Number of yellow cards
            red_cards: Number of red cards
            corner_kicks: Number of corner kicks

        Returns:
            MatchStats instance
        """
        # Validate club is in match
        if club.id not in (match.home_club_id, match.away_club_id):
            raise MatchReportError(f"{club.name} is not in this match")

        # Validate percentages
        if possession is not None and (possession < 0 or possession > 100):
            raise MatchReportError("Possession must be between 0 and 100")

        if passes_accuracy is not None and (passes_accuracy < 0 or passes_accuracy > 100):
            raise MatchReportError("Pass accuracy must be between 0 and 100")

        stats, _ = MatchStats.objects.get_or_create(
            match=match,
            club=club
        )

        # Update provided fields
        if possession is not None:
            stats.possession = possession
        if shots_on_goal is not None:
            stats.shots_on_goal = shots_on_goal
        if shots_off_goal is not None:
            stats.shots_off_goal = shots_off_goal
        if passes is not None:
            stats.passes = passes
        if passes_accuracy is not None:
            stats.passes_accuracy = passes_accuracy
        if fouls is not None:
            stats.fouls = fouls
        if yellow_cards is not None:
            stats.yellow_cards = yellow_cards
        if red_cards is not None:
            stats.red_cards = red_cards
        if corner_kicks is not None:
            stats.corner_kicks = corner_kicks

        stats.save()
        return stats

    @staticmethod
    def get_team_stats(
        *,
        tenant: Tenant,
        match: Match,
        club: Club
    ) -> Optional[MatchStats]:
        """Get team statistics for a match."""
        try:
            return MatchStats.objects.get(match=match, club=club)
        except MatchStats.DoesNotExist:
            return None

    @staticmethod
    def get_match_statistics(
        *,
        tenant: Tenant,
        match: Match
    ) -> dict:
        """
        Get complete statistics for both teams in a match.

        Returns:
            Dict with home_team and away_team statistics
        """
        home_stats = MatchReportService.get_team_stats(
            tenant=tenant,
            match=match,
            club=match.home_club
        )

        away_stats = MatchReportService.get_team_stats(
            tenant=tenant,
            match=match,
            club=match.away_club
        )

        return {
            "home_team": {
                "club": match.home_club.name,
                "stats": MatchReportService._stats_to_dict(home_stats)
            },
            "away_team": {
                "club": match.away_club.name,
                "stats": MatchReportService._stats_to_dict(away_stats)
            }
        }

    # ─── Player Performance Updates ────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def finalize_player_statistics(
        *,
        tenant: Tenant,
        match: Match,
        updates: List[dict],
    ) -> List[MatchLineup]:
        """
        Update player performance after match completes.

        Args:
            tenant: Organization
            match: Match instance
            updates: List of dicts with player_id, club_id, minutes_played,
                    substituted_in_minute, substituted_out_minute

        Returns:
            List of updated MatchLineup instances
        """
        updated_entries = []

        for update in updates:
            try:
                player = Player.objects.get(
                    id=update['player_id'],
                    tenant=tenant
                )
                club = Club.objects.get(
                    id=update['club_id'],
                    tenant=tenant
                )

                lineup = MatchLineup.objects.get(
                    match=match,
                    player=player,
                    club=club
                )

                # Update minutes
                lineup.minutes_played = update.get('minutes_played', 0)

                if 'substituted_in_minute' in update:
                    lineup.substituted_in_minute = update['substituted_in_minute']

                if 'substituted_out_minute' in update:
                    lineup.substituted_out_minute = update['substituted_out_minute']

                lineup.save()
                updated_entries.append(lineup)

            except (Player.DoesNotExist, Club.DoesNotExist, MatchLineup.DoesNotExist):
                continue

        return updated_entries

    # ─── Report Summary ───────────────────────────────────────────────────

    @staticmethod
    def get_report_summary(
        *,
        tenant: Tenant,
        match: Match
    ) -> dict:
        """
        Get complete match report summary with all details.

        Returns:
            Dict with score, goals, statistics, and lineups
        """
        report = MatchReportService.get_report(tenant=tenant, match=match)
        goals = MatchReportService.get_match_goals(tenant=tenant, match=match)
        stats = MatchReportService.get_match_statistics(tenant=tenant, match=match)

        # Group goals by team
        home_goals = [g for g in goals if g.club_id == match.home_club_id]
        away_goals = [g for g in goals if g.club_id == match.away_club_id]

        return {
            "match": {
                "id": str(match.id),
                "home_club": match.home_club.name,
                "away_club": match.away_club.name,
                "scheduled_for": match.match_date,
                "match_status": match.get_status_display(),
            },
            "report": {
                "home_score": report.home_score if report else 0,
                "away_score": report.away_score if report else 0,
                "match_duration": report.match_duration if report else None,
                "status": report.get_status_display() if report else "pending",
            },
            "goals": {
                "home": MatchReportService._goals_to_list(home_goals),
                "away": MatchReportService._goals_to_list(away_goals),
            },
            "statistics": stats,
        }

    # ─── Helper Methods ───────────────────────────────────────────────────

    @staticmethod
    def _stats_to_dict(stats: Optional[MatchStats]) -> dict:
        """Convert MatchStats to dictionary."""
        if not stats:
            return {
                "possession": None,
                "shots_on_goal": None,
                "shots_off_goal": None,
                "passes": None,
                "passes_accuracy": None,
                "fouls": None,
                "yellow_cards": None,
                "red_cards": None,
                "corner_kicks": None,
            }

        return {
            "possession": stats.possession,
            "shots_on_goal": stats.shots_on_goal,
            "shots_off_goal": stats.shots_off_goal,
            "passes": stats.passes,
            "passes_accuracy": stats.passes_accuracy,
            "fouls": stats.fouls,
            "yellow_cards": stats.yellow_cards,
            "red_cards": stats.red_cards,
            "corner_kicks": stats.corner_kicks,
        }

    @staticmethod
    def _goals_to_list(goals: List[Goal]) -> list:
        """Convert Goal instances to list of dicts."""
        return [
            {
                "id": str(goal.id),
                "player": goal.player.full_name,
                "minute": goal.minute,
                "goal_type": goal.get_goal_type_display(),
                "assist_player": goal.assist_player.full_name if goal.assist_player else None,
            }
            for goal in goals
        ]
