"""
BOLAYETU — Player Medical Service Tests

Tests for PlayerMedicalService methods.
"""

from django.test import TestCase
from datetime import date, timedelta

from players.models import Player, PlayerMedicalProfile, MedicalDocument
from players.services.medical_service import PlayerMedicalService
from core.models import Tenant


class PlayerMedicalServiceTestCase(TestCase):
    """Test PlayerMedicalService methods."""

    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Org", slug="test-org")
        self.player = Player.objects.create(
            first_name="Medical",
            last_name="Player",
            date_of_birth=date(1995, 5, 15),
            nationality="AO",
            primary_position="CM",
        )

    def test_create_medical_profile(self):
        """Test creating a medical profile for a player."""
        profile = PlayerMedicalService.create_or_update_medical_profile(
            player=self.player,
            blood_type=PlayerMedicalProfile.BloodType.A_POSITIVE,
            medical_status=PlayerMedicalProfile.MedicalStatus.FIT,
            medical_clearance=True,
        )

        self.assertEqual(profile.player, self.player)
        self.assertEqual(profile.blood_type, PlayerMedicalProfile.BloodType.A_POSITIVE)
        self.assertEqual(profile.medical_status, PlayerMedicalProfile.MedicalStatus.FIT)
        self.assertTrue(profile.medical_clearance)
        self.assertTrue(profile.is_fit_to_play)

    def test_update_medical_profile(self):
        """Test updating an existing medical profile."""
        # Create initial profile
        PlayerMedicalService.create_or_update_medical_profile(
            player=self.player,
            medical_status=PlayerMedicalProfile.MedicalStatus.FIT,
        )

        # Update profile
        updated = PlayerMedicalService.create_or_update_medical_profile(
            player=self.player,
            medical_status=PlayerMedicalProfile.MedicalStatus.INJURED,
            injury_status="Hamstring strain - right leg",
            medical_clearance=False,
        )

        self.assertEqual(updated.medical_status, PlayerMedicalProfile.MedicalStatus.INJURED)
        self.assertEqual(updated.injury_status, "Hamstring strain - right leg")
        self.assertFalse(updated.medical_clearance)
        self.assertFalse(updated.is_fit_to_play)

    def test_update_medical_status(self):
        """Test updating just medical status."""
        PlayerMedicalService.create_or_update_medical_profile(
            player=self.player,
        )

        updated = PlayerMedicalService.update_medical_status(
            player=self.player,
            medical_status=PlayerMedicalProfile.MedicalStatus.RECOVERING,
            injury_status="Recovering from ACL surgery",
        )

        self.assertEqual(updated.medical_status, PlayerMedicalProfile.MedicalStatus.RECOVERING)
        self.assertIn("ACL", updated.injury_status)

    def test_add_medical_document(self):
        """Test adding a medical document."""
        document = PlayerMedicalService.add_medical_document(
            player=self.player,
            document_type=MedicalDocument.DocumentType.MEDICAL_CERTIFICATE,
            title="Medical Clearance Certificate",
            issued_at=date.today(),
            expires_at=date.today() + timedelta(days=365),
        )

        self.assertEqual(document.player, self.player)
        self.assertEqual(document.document_type, MedicalDocument.DocumentType.MEDICAL_CERTIFICATE)
        self.assertEqual(document.verification_status, MedicalDocument.VerificationStatus.PENDING)
        self.assertTrue(document.is_confidential)

    def test_verify_medical_document(self):
        """Test verifying a medical document."""
        document = PlayerMedicalService.add_medical_document(
            player=self.player,
            document_type=MedicalDocument.DocumentType.PHYSICAL_EXAM,
            title="Annual Physical",
            issued_at=date.today(),
        )

        self.assertEqual(document.verification_status, MedicalDocument.VerificationStatus.PENDING)

        verified = PlayerMedicalService.verify_medical_document(
            document=document,
            verified_by=None,  # In real test, would pass a User instance
        )

        self.assertEqual(verified.verification_status, MedicalDocument.VerificationStatus.VERIFIED)
        self.assertIsNotNone(verified.verified_at)

    def test_reject_medical_document(self):
        """Test rejecting a medical document."""
        document = PlayerMedicalService.add_medical_document(
            player=self.player,
            document_type=MedicalDocument.DocumentType.LAB_RESULT,
            title="Blood Test",
            issued_at=date.today(),
        )

        rejected = PlayerMedicalService.reject_medical_document(
            document=document,
            rejected_by=None,
            reason="Document is incomplete",
        )

        self.assertEqual(rejected.verification_status, MedicalDocument.VerificationStatus.REJECTED)

    def test_get_medical_history(self):
        """Test getting complete medical history."""
        # Create profile
        PlayerMedicalService.create_or_update_medical_profile(
            player=self.player,
            medical_status=PlayerMedicalProfile.MedicalStatus.FIT,
            medical_clearance=True,
        )

        # Add documents
        PlayerMedicalService.add_medical_document(
            player=self.player,
            document_type=MedicalDocument.DocumentType.MEDICAL_CERTIFICATE,
            title="Certificate 1",
            issued_at=date.today(),
        )
        PlayerMedicalService.add_medical_document(
            player=self.player,
            document_type=MedicalDocument.DocumentType.INJURY_REPORT,
            title="Injury Report",
            issued_at=date.today(),
        )

        history = PlayerMedicalService.get_medical_history(self.player)

        self.assertIsNotNone(history["profile"])
        self.assertEqual(len(history["documents"]), 2)
        self.assertTrue(history["is_fit_to_play"])

    def test_verify_medical_clearance(self):
        """Test medical clearance verification."""
        # No profile = not cleared
        self.assertFalse(PlayerMedicalService.verify_medical_clearance(self.player))

        # Create profile without clearance
        PlayerMedicalService.create_or_update_medical_profile(
            player=self.player,
            medical_status=PlayerMedicalProfile.MedicalStatus.FIT,
            medical_clearance=False,
        )
        self.assertFalse(PlayerMedicalService.verify_medical_clearance(self.player))

        # Grant clearance
        PlayerMedicalService.create_or_update_medical_profile(
            player=self.player,
            medical_clearance=True,
        )
        self.assertTrue(PlayerMedicalService.verify_medical_clearance(self.player))

    def test_medical_exam_due(self):
        """Test checking if player needs medical exam."""
        # Create profile with future exam date
        profile = PlayerMedicalService.create_or_update_medical_profile(
            player=self.player,
            next_medical_exam=date.today() + timedelta(days=30),
        )
        self.assertFalse(profile.needs_medical_exam)

        # Set past exam date
        profile = PlayerMedicalService.create_or_update_medical_profile(
            player=self.player,
            next_medical_exam=date.today() - timedelta(days=1),
        )
        self.assertTrue(profile.needs_medical_exam)

    def test_document_expiration(self):
        """Test document expiration check."""
        # Create document that expires in the future
        future_doc = PlayerMedicalService.add_medical_document(
            player=self.player,
            document_type=MedicalDocument.DocumentType.MEDICAL_CERTIFICATE,
            title="Valid Certificate",
            issued_at=date.today(),
            expires_at=date.today() + timedelta(days=30),
        )
        PlayerMedicalService.verify_medical_document(future_doc, verified_by=None)
        self.assertTrue(future_doc.is_valid)
        self.assertFalse(future_doc.is_expired)

        # Create expired document
        expired_doc = PlayerMedicalService.add_medical_document(
            player=self.player,
            document_type=MedicalDocument.DocumentType.MEDICAL_CERTIFICATE,
            title="Expired Certificate",
            issued_at=date.today() - timedelta(days=365),
            expires_at=date.today() - timedelta(days=1),
        )
        PlayerMedicalService.verify_medical_document(expired_doc, verified_by=None)
        self.assertFalse(expired_doc.is_valid)
        self.assertTrue(expired_doc.is_expired)
