"""
BOLAYETU — Clubs Serializers
"""

from clubs.serializers.club import (
    ClubCreateSerializer,
    ClubKpisSerializer,
    ClubLogoUploadSerializer,
    ClubMemberSerializer,
    ClubSerializer,
    ClubSquadMemberSerializer,
    ClubStaffSerializer,
    ClubUpdateSerializer,
    PublicClubSerializer,
)
from clubs.serializers.club_affiliation_request import (
    ClubAffiliationRequestSerializer,
    ClubAffiliationRequestCreateSerializer,
    ClubAffiliationRequestReviewSerializer,
)

__all__ = [
    "ClubSerializer",
    "ClubCreateSerializer",
    "ClubUpdateSerializer",
    "ClubLogoUploadSerializer",
    "PublicClubSerializer",
    "ClubKpisSerializer",
    "ClubMemberSerializer",
    "ClubSquadMemberSerializer",
    "ClubStaffSerializer",
    "ClubAffiliationRequestSerializer",
    "ClubAffiliationRequestCreateSerializer",
    "ClubAffiliationRequestReviewSerializer",
]
