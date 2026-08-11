"""Players domain models."""

from players.models.player import Player
from players.models.registration import PlayerRegistration
from players.models.player_registration_request import PlayerRegistrationRequest
from players.models.player_video import PlayerVideo
from players.models.player_document import PlayerDocument
from players.models.player_achievement import PlayerAchievement
from players.models.career import PlayerCareer
from players.models.statistics import PlayerSeasonStatistics
from players.models.football_profile import PlayerFootballProfile

# Phase 1 models
from players.models.identity import PlayerIdentityDocument
from players.models.contact import PlayerContact, EmergencyContact
from players.models.guardian import LegalGuardian
from players.models.external_id import PlayerExternalId
from players.models.privacy import PlayerPrivacySettings
from players.models.onboarding import PlayerOnboardingStatus
from players.models.invite import PlayerInvite

# Phase 3 models (Professional)
from players.models.contract import PlayerContract
from players.models.agent import Agent, PlayerAgentRelationship
from players.models.training import PlayerTrainingHistory

__all__ = [
    "Player",
    "PlayerRegistration",
    "PlayerRegistrationRequest",
    "PlayerVideo",
    "PlayerDocument",
    "PlayerAchievement",
    "PlayerCareer",
    "PlayerSeasonStatistics",
    "PlayerFootballProfile",
    # Phase 1 additions
    "PlayerIdentityDocument",
    "PlayerContact",
    "EmergencyContact",
    "LegalGuardian",
    "PlayerExternalId",
    "PlayerPrivacySettings",
    "PlayerOnboardingStatus",
    "PlayerInvite",
    # Phase 3 additions
    "PlayerContract",
    "Agent",
    "PlayerAgentRelationship",
    "PlayerTrainingHistory",
]
