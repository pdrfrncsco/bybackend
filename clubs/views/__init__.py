"""
BOLAYETU — Clubs Views Package
"""

from clubs.views.club_views import (
    ClubMeView,
    ClubLogoView,
    ClubCreateView,
    ClubPublicListView,
    ClubPublicDetailView,
    ClubKpisView,
    ClubSquadView,
    ClubStaffView,
    ClubMembersView,
    ClubMemberDetailView,
    ClubActivateView,
    ClubSuspendView,
)
from clubs.views.club_assets_views import (
    ClubDocumentsView,
    ClubDocumentDetailView,
    ClubPublicDocumentsView,
    ClubSponsorsView,
    ClubSponsorDetailView,
    ClubPublicSponsorsView,
)
from clubs.views.transfer_views import (
    TransferViewSet,
)
from clubs.views.player_registration_request_views import (
    ClubMePlayerRegistrationRequestsView,
    ClubMePlayerRegistrationRequestReviewView,
)

__all__ = [
    "ClubMeView",
    "ClubLogoView",
    "ClubCreateView",
    "ClubPublicListView",
    "ClubPublicDetailView",
    "ClubKpisView",
    "ClubSquadView",
    "ClubStaffView",
    "ClubMembersView",
    "ClubMemberDetailView",
    "ClubActivateView",
    "ClubSuspendView",
    "ClubDocumentsView",
    "ClubDocumentDetailView",
    "ClubPublicDocumentsView",
    "ClubSponsorsView",
    "ClubSponsorDetailView",
    "ClubPublicSponsorsView",
    "TransferViewSet",
    "ClubMePlayerRegistrationRequestsView",
    "ClubMePlayerRegistrationRequestReviewView",
]
