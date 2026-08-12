"""
PlayerMedicalService

Handles medical profile management for players.
Critical for player health, fitness tracking, and regulatory compliance.

Privacy Note: Access restricted to Player, Club Medical Staff, and Authorized Organization only.
"""

import logging
from datetime import date
from typing import Optional

from django.db import transaction
from django.utils import timezone

from players.models import Player, PlayerMedicalProfile, MedicalDocument

logger = logging.getLogger("players")


class PlayerMedicalService:
    """Service for managing player medical profiles and documents."""

    @staticmethod
    @transaction.atomic
    def create_or_update_medical_profile(
        player: Player,
        blood_type: Optional[str] = None,
        medical_status: Optional[str] = None,
        medical_clearance: Optional[bool] = None,
        fitness_status: Optional[str] = None,
        injury_status: Optional[str] = None,
        medical_notes: Optional[str] = None,
        last_medical_exam: Optional[date] = None,
        next_medical_exam: Optional[date] = None,
        allergies: Optional[str] = None,
        current_medications: Optional[str] = None,
        medical_conditions: Optional[str] = None,
    ) -> PlayerMedicalProfile:
        """Create or update a player's medical profile.

        Creates a new profile if none exists, otherwise updates the existing one.
        All fields are optional - only provided fields are updated.

        Args:
            player: Player instance
            blood_type: Blood type (A+, A-, B+, B-, AB+, AB-, O+, O-, unknown)
            medical_status: Medical status (fit, injured, recovering, suspended_medical)
            medical_clearance: Whether player is medically cleared to play
            fitness_status: General fitness assessment
            injury_status: Current injury description
            medical_notes: Confidential medical notes (restricted access)
            last_medical_exam: Date of last medical exam
            next_medical_exam: Date of next scheduled medical exam
            allergies: Known allergies
            current_medications: Current medications
            medical_conditions: Pre-existing medical conditions

        Returns:
            PlayerMedicalProfile instance
        """
        profile, created = PlayerMedicalProfile.objects.get_or_create(
            player=player,
            defaults={
                "blood_type": blood_type or PlayerMedicalProfile.BloodType.UNKNOWN,
                "medical_status": medical_status or PlayerMedicalProfile.MedicalStatus.FIT,
            },
        )

        # Update fields if provided
        update_fields = []
        
        if blood_type is not None:
            profile.blood_type = blood_type
            update_fields.append("blood_type")
        
        if medical_status is not None:
            profile.medical_status = medical_status
            update_fields.append("medical_status")
        
        if medical_clearance is not None:
            profile.medical_clearance = medical_clearance
            update_fields.append("medical_clearance")
        
        if fitness_status is not None:
            profile.fitness_status = fitness_status
            update_fields.append("fitness_status")
        
        if injury_status is not None:
            profile.injury_status = injury_status
            update_fields.append("injury_status")
        
        if medical_notes is not None:
            profile.medical_notes = medical_notes
            update_fields.append("medical_notes")
        
        if last_medical_exam is not None:
            profile.last_medical_exam = last_medical_exam
            update_fields.append("last_medical_exam")
        
        if next_medical_exam is not None:
            profile.next_medical_exam = next_medical_exam
            update_fields.append("next_medical_exam")
        
        if allergies is not None:
            profile.allergies = allergies
            update_fields.append("allergies")
        
        if current_medications is not None:
            profile.current_medications = current_medications
            update_fields.append("current_medications")
        
        if medical_conditions is not None:
            profile.medical_conditions = medical_conditions
            update_fields.append("medical_conditions")

        if update_fields:
            profile.save(update_fields=update_fields)

        action = "Created" if created else "Updated"
        logger.info("%s medical profile for player: %s", action, player.full_name)

        return profile

    @staticmethod
    @transaction.atomic
    def update_medical_status(
        player: Player,
        medical_status: str,
        injury_status: Optional[str] = None,
        medical_clearance: Optional[bool] = None,
    ) -> PlayerMedicalProfile:
        """Update player's medical status.

        Commonly used after injury updates or medical exams.

        Args:
            player: Player instance
            medical_status: New medical status
            injury_status: Optional injury description
            medical_clearance: Optional clearance status

        Returns:
            Updated PlayerMedicalProfile
        """
        profile = PlayerMedicalProfile.objects.filter(player=player).first()
        
        if not profile:
            return PlayerMedicalService.create_or_update_medical_profile(
                player=player,
                medical_status=medical_status,
                injury_status=injury_status,
                medical_clearance=medical_clearance,
            )

        profile.medical_status = medical_status
        
        if injury_status is not None:
            profile.injury_status = injury_status
        
        if medical_clearance is not None:
            profile.medical_clearance = medical_clearance

        profile.save()

        logger.info(
            "Updated medical status for %s: %s (clearance: %s)",
            player.full_name,
            medical_status,
            medical_clearance,
        )

        return profile

    @staticmethod
    @transaction.atomic
    def add_medical_document(
        player: Player,
        document_type: str,
        title: str,
        issued_at: date,
        file=None,
        expires_at: Optional[date] = None,
        description: Optional[str] = None,
        is_confidential: bool = True,
    ) -> MedicalDocument:
        """Add a medical document for a player.

        Args:
            player: Player instance
            document_type: Type of document (medical_certificate, injury_report, etc.)
            title: Document title
            issued_at: Date document was issued
            file: Optional MediaAsset file reference
            expires_at: Optional expiration date
            description: Optional description
            is_confidential: Whether document is confidential (default: True)

        Returns:
            MedicalDocument instance
        """
        document = MedicalDocument.objects.create(
            player=player,
            document_type=document_type,
            title=title,
            issued_at=issued_at,
            file=file,
            expires_at=expires_at,
            description=description or "",
            is_confidential=is_confidential,
            verification_status=MedicalDocument.VerificationStatus.PENDING,
        )

        logger.info(
            "Added medical document for %s: %s (%s)",
            player.full_name,
            title,
            document_type,
        )

        return document

    @staticmethod
    @transaction.atomic
    def verify_medical_document(
        document: MedicalDocument,
        verified_by,
    ) -> MedicalDocument:
        """Verify a medical document.

        Args:
            document: MedicalDocument instance
            verified_by: User verifying the document

        Returns:
            Verified MedicalDocument
        """
        document.verification_status = MedicalDocument.VerificationStatus.VERIFIED
        document.verified_by = verified_by
        document.verified_at = timezone.now()
        document.save(update_fields=["verification_status", "verified_by", "verified_at"])

        logger.info(
            "Verified medical document %s for %s by %s",
            document.title,
            document.player.full_name,
            verified_by,
        )

        return document

    @staticmethod
    @transaction.atomic
    def reject_medical_document(
        document: MedicalDocument,
        rejected_by,
        reason: Optional[str] = None,
    ) -> MedicalDocument:
        """Reject a medical document.

        Args:
            document: MedicalDocument instance
            rejected_by: User rejecting the document
            reason: Optional rejection reason

        Returns:
            Rejected MedicalDocument
        """
        document.verification_status = MedicalDocument.VerificationStatus.REJECTED
        document.verified_by = rejected_by
        document.verified_at = timezone.now()
        if reason:
            document.description = f"{document.description}\n\nRejection reason: {reason}".strip()
        document.save()

        logger.info(
            "Rejected medical document %s for %s by %s: %s",
            document.title,
            document.player.full_name,
            rejected_by,
            reason or "no reason provided",
        )

        return document

    @staticmethod
    def get_medical_history(player: Player) -> dict:
        """Get complete medical history for a player.

        Returns:
            {
                "profile": PlayerMedicalProfile,
                "documents": List[MedicalDocument],
                "is_fit_to_play": bool,
                "pending_exams": bool,
            }
        """
        profile = PlayerMedicalProfile.objects.filter(player=player).first()
        documents = MedicalDocument.objects.filter(player=player).order_by("-issued_at")

        return {
            "profile": profile,
            "documents": list(documents),
            "is_fit_to_play": profile.is_fit_to_play if profile else False,
            "pending_exams": profile.needs_medical_exam if profile else False,
        }

    @staticmethod
    def verify_medical_clearance(player: Player) -> bool:
        """Check if player has valid medical clearance.

        Returns:
            True if player is medically cleared to play.
        """
        profile = PlayerMedicalProfile.objects.filter(player=player).first()
        
        if not profile:
            return False

        return profile.is_fit_to_play

    @staticmethod
    def get_players_requiring_exams(tenant=None) -> list:
        """Get list of players who need medical exams.

        Args:
            tenant: Optional tenant filter

        Returns:
            List of Player instances requiring medical exams
        """
        from datetime import date

        profiles = PlayerMedicalProfile.objects.filter(
            next_medical_exam__lte=date.today(),
            medical_clearance=True,
        ).select_related("player")

        if tenant:
            # Filter by tenant through player's registrations
            profiles = profiles.filter(
                player__registrations__tenant=tenant,
                player__registrations__status__in=[
                    "registered",
                    "loaned",
                ],
            ).distinct()

        return [p.player for p in profiles]


class MedicalServiceError(Exception):
    """Raised when a medical service operation fails."""
    pass
