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
from clubs.serializers.club_document import ClubDocumentCreateSerializer, ClubDocumentSerializer
from clubs.serializers.club_sponsor import ClubSponsorCreateSerializer, ClubSponsorSerializer, ClubSponsorUpdateSerializer
from clubs.serializers.transfer_serializers import (
    TransferCreateSerializer,
    TransferSerializer,
    TransferListSerializer,
    TransferApproveSerializer,
    TransferRejectSerializer,
    TransferCancelSerializer,
    LoanExtendSerializer,
    LoanReturnSerializer,
    LoanMakePermanentSerializer,
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
    "ClubDocumentSerializer",
    "ClubDocumentCreateSerializer",
    "ClubSponsorSerializer",
    "ClubSponsorCreateSerializer",
    "ClubSponsorUpdateSerializer",
    "TransferCreateSerializer",
    "TransferSerializer",
    "TransferListSerializer",
    "TransferApproveSerializer",
    "TransferRejectSerializer",
    "TransferCancelSerializer",
    "LoanExtendSerializer",
    "LoanReturnSerializer",
    "LoanMakePermanentSerializer",
]
