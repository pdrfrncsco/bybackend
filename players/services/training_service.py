"""
PlayerTrainingHistoryService

Handles training/development history for players.
Critical for calculating EPP (Education & Productivity Payouts) and Solidarity Contribution
in international transfers (FIFA RSTP).
"""

import logging
from datetime import date
from typing import Optional, List

from django.db import transaction

from players.models import Player, PlayerTrainingHistory

logger = logging.getLogger("players")


class PlayerTrainingHistoryService:
    """Service for managing player training history.

    This is essential for:
    - Training Compensation calculations
    - Solidarity Contribution calculations
    - FIFA Connect integration
    - Career timeline reconstruction
    """

    @staticmethod
    @transaction.atomic
    def add_training_entry(
        player: Player,
        start_date: date,
        country: str,
        training_category: str = PlayerTrainingHistory.TrainingCategory.AMATEUR,
        club=None,
        academy_name: str = "",
        end_date: Optional[date] = None,
        training_certificate=None,
        notes: str = "",
    ) -> PlayerTrainingHistory:
        """Add a training history entry for a player.

        Either club or academy_name should be provided.

        Raises TrainingHistoryError if validation fails.
        """
        if not club and not academy_name:
            raise TrainingHistoryError(
                "Either club or academy_name must be provided."
            )

        # Check for overlapping entries with the same club/academy
        existing = PlayerTrainingHistory.objects.filter(
            player=player,
            club=club if club else None,
            academy_name=academy_name if academy_name else "",
        ).first()

        if existing:
            # Check for date overlap
            if existing.end_date is None or end_date is None:
                # If any of the periods is open-ended, check start overlap
                if existing.start_date <= start_date:
                    if existing.end_date is None or start_date <= existing.end_date:
                        raise TrainingHistoryError(
                            f"Overlapping training entry already exists for this player at {club.name if club else academy_name}."
                        )
            elif existing.start_date <= end_date and start_date <= existing.end_date:
                raise TrainingHistoryError(
                    f"Overlapping training entry already exists for this player at {club.name if club else academy_name}."
                )

        entry = PlayerTrainingHistory.objects.create(
            player=player,
            club=club,
            academy_name=academy_name,
            country=country,
            training_category=training_category,
            start_date=start_date,
            end_date=end_date,
            training_certificate=training_certificate,
            notes=notes,
        )

        entity_name = club.name if club else academy_name
        logger.info(
            "Training history added: %s @ %s (%s–%s)",
            player.full_name,
            entity_name,
            start_date,
            end_date or "present",
        )
        return entry

    @staticmethod
    @transaction.atomic
    def verify_training_entry(
        entry: PlayerTrainingHistory,
        verified_by,
    ) -> PlayerTrainingHistory:
        """Verify a training history entry.

        Verification is required for:
        - Training Compensation calculations
        - Solidarity Contribution distribution
        - FIFA Connect sync
        """
        from django.utils import timezone

        entry.verified = True
        entry.verified_by = verified_by
        entry.verified_at = timezone.now()
        entry.save(update_fields=["verified", "verified_by", "verified_at"])

        entity_name = entry.club.name if entry.club else entry.academy_name
        logger.info(
            "Training history verified: %s @ %s by %s",
            entry.player.full_name,
            entity_name,
            verified_by,
        )
        return entry

    @staticmethod
    @transaction.atomic
    def end_training_entry(
        entry: PlayerTrainingHistory,
        end_date: Optional[date] = None,
    ) -> PlayerTrainingHistory:
        """End an ongoing training entry."""
        from datetime import date as date_class

        entry.end_date = end_date or date_class.today()
        entry.save(update_fields=["end_date"])

        entity_name = entry.club.name if entry.club else entry.academy_name
        logger.info(
            "Training history ended: %s @ %s (ended: %s)",
            entry.player.full_name,
            entity_name,
            entry.end_date,
        )
        return entry

    @staticmethod
    def get_training_timeline(player: Player) -> List[PlayerTrainingHistory]:
        """Get complete training timeline for a player, ordered chronologically."""
        return list(
            PlayerTrainingHistory.objects.filter(player=player)
            .select_related("club")
            .order_by("start_date")
        )

    @staticmethod
    def get_training_by_category(
        player: Player,
        category: str,
    ) -> List[PlayerTrainingHistory]:
        """Get training history filtered by category."""
        return list(
            PlayerTrainingHistory.objects.filter(
                player=player,
                training_category=category,
            )
            .select_related("club")
            .order_by("-start_date")
        )

    @staticmethod
    def get_training_years_by_club(
        player: Player,
        club_id: str,
    ) -> float:
        """Calculate total training years at a specific club.

        Used for Solidarity Contribution calculations.
        """
        entries = PlayerTrainingHistory.objects.filter(
            player=player,
            club_id=club_id,
        )

        total_days = 0
        for entry in entries:
            end = entry.end_date or date.today()
            days = (end - entry.start_date).days
            if days > 0:
                total_days += days

        return total_days / 365.25

    @staticmethod
    def get_training_compensation_data(player: Player) -> dict:
        """Get training data needed for Training Compensation calculations.

        Returns:
            {
                "total_years": float,
                "clubs": [
                    {
                        "club_id": str,
                        "club_name": str,
                        "years": float,
                        "category": str,
                        "country": str,
                        "verified": bool,
                    },
                    ...
                ]
            }
        """
        entries = PlayerTrainingHistory.objects.filter(player=player).select_related("club")

        clubs_data = {}
        total_years = 0.0

        for entry in entries:
            end = entry.end_date or date.today()
            years = (end - entry.start_date).days / 365.25
            total_years += years

            club_key = str(entry.club_id) if entry.club else entry.academy_name
            if club_key not in clubs_data:
                clubs_data[club_key] = {
                    "club_id": str(entry.club_id) if entry.club else None,
                    "club_name": entry.club.name if entry.club else entry.academy_name,
                    "years": years,
                    "category": entry.training_category,
                    "country": entry.country,
                    "verified": entry.verified,
                    "start_date": entry.start_date.isoformat(),
                    "end_date": entry.end_date.isoformat() if entry.end_date else None,
                }
            else:
                # Sum years if multiple entries for same club
                clubs_data[club_key]["years"] += years

        return {
            "total_years": round(total_years, 2),
            "clubs": list(clubs_data.values()),
        }

    @staticmethod
    @transaction.atomic
    def import_training_history(
        player: Player,
        training_data: List[dict],
    ) -> List[PlayerTrainingHistory]:
        """Import multiple training history entries at once.

        Used for bulk import during onboarding or data migration.

        Args:
            player: Player instance
            training_data: List of dicts with keys:
                - start_date (required)
                - country (required)
                - club_id (optional)
                - academy_name (optional if no club_id)
                - training_category (default: amateur)
                - end_date (optional)
                - notes (optional)

        Returns:
            List of created PlayerTrainingHistory instances
        """
        from clubs.models import Club

        entries = []
        for data in training_data:
            club = None
            if data.get("club_id"):
                try:
                    club = Club.objects.get(id=data["club_id"])
                except Club.DoesNotExist:
                    logger.warning(
                        "Club %s not found during training history import for player %s",
                        data["club_id"],
                        player.id,
                    )
                    continue

            entry = PlayerTrainingHistoryService.add_training_entry(
                player=player,
                start_date=data["start_date"],
                country=data["country"],
                training_category=data.get(
                    "training_category",
                    PlayerTrainingHistory.TrainingCategory.AMATEUR,
                ),
                club=club,
                academy_name=data.get("academy_name", ""),
                end_date=data.get("end_date"),
                notes=data.get("notes", ""),
            )
            entries.append(entry)

        logger.info(
            "Imported %d training history entries for player %s",
            len(entries),
            player.full_name,
        )
        return entries


class TrainingHistoryError(Exception):
    """Raised when a training history operation fails."""
    pass
