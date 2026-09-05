"""
BOLAYETU — Clubs URL Configuration

All club endpoints are under /api/v1/clubs/.
"""

from django.urls import path
from rest_framework.routers import DefaultRouter

from clubs.views import (
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
    ClubDocumentsView,
    ClubDocumentDetailView,
    ClubPublicDocumentsView,
    ClubSponsorsView,
    ClubSponsorDetailView,
    ClubPublicSponsorsView,
    ClubMePlayerRegistrationRequestsView,
    ClubMePlayerRegistrationRequestReviewView,
    ClubPublicCompetitionsView,
    ClubPublicMatchesView,
    ClubPublicStandingsView,
    ClubMeCompetitionsView,
    ClubMeMatchesView,
    ClubMeStandingsView,
    TransferViewSet,
)
from competitions.views.competition_views import ClubCompetitionListView

router = DefaultRouter()
router.register(r"transfers", TransferViewSet, basename="transfer")

urlpatterns = router.urls + [
    # Authenticated — Club Management
    path("me/", ClubMeView.as_view(), name="club-me"),
    path("me/logo/", ClubLogoView.as_view(), name="club-logo"),
    path("me/competitions/", ClubMeCompetitionsView.as_view(), name="club-me-competitions"),
    path("me/matches/", ClubMeMatchesView.as_view(), name="club-me-matches"),
    path("me/standings/", ClubMeStandingsView.as_view(), name="club-me-standings"),
    path("me/player-registration-requests/", ClubMePlayerRegistrationRequestsView.as_view(), name="club-me-player-registration-requests"),
    path("me/player-registration-requests/<uuid:request_id>/", ClubMePlayerRegistrationRequestReviewView.as_view(), name="club-me-player-registration-request-review"),
    path("<uuid:club_id>/player-registration-requests/", ClubMePlayerRegistrationRequestsView.as_view(), name="club-player-registration-requests"),
    path(
        "<uuid:club_id>/player-registration-requests/<uuid:request_id>/",
        ClubMePlayerRegistrationRequestReviewView.as_view(),
        name="club-player-registration-request-review",
    ),
    path("", ClubCreateView.as_view(), name="club-create"),

    # Authenticated — Club Status Management
    path("<slug:slug>/activate/", ClubActivateView.as_view(), name="club-activate"),
    path("<slug:slug>/suspend/", ClubSuspendView.as_view(), name="club-suspend"),

    # Authenticated — Member Management
    path("<slug:slug>/members/", ClubMembersView.as_view(), name="club-members"),
    path("<slug:slug>/members/<uuid:member_id>/", ClubMemberDetailView.as_view(), name="club-member-detail"),
    path("<slug:slug>/documents/", ClubDocumentsView.as_view(), name="club-documents"),
    path("<slug:slug>/documents/<uuid:document_id>/", ClubDocumentDetailView.as_view(), name="club-document-detail"),
    path("<slug:slug>/sponsors/", ClubSponsorsView.as_view(), name="club-sponsors"),
    path("<slug:slug>/sponsors/<uuid:sponsor_id>/", ClubSponsorDetailView.as_view(), name="club-sponsor-detail"),

    # Public — Club Discovery
    path("public/", ClubPublicListView.as_view(), name="club-public-list"),
    path("public/<slug:slug>/", ClubPublicDetailView.as_view(), name="club-public-detail"),
    path("public/<slug:slug>/kpis/", ClubKpisView.as_view(), name="club-kpis"),
    path("public/<slug:slug>/squad/", ClubSquadView.as_view(), name="club-squad"),
    path("public/<slug:slug>/staff/", ClubStaffView.as_view(), name="club-staff"),
    path("public/<slug:slug>/documents/", ClubPublicDocumentsView.as_view(), name="club-public-documents"),
    path("public/<slug:slug>/sponsors/", ClubPublicSponsorsView.as_view(), name="club-public-sponsors"),
    path("public/<slug:slug>/competitions/", ClubPublicCompetitionsView.as_view(), name="club-public-competitions"),
    path("public/<slug:slug>/matches/", ClubPublicMatchesView.as_view(), name="club-public-matches"),
    path("public/<slug:slug>/standings/", ClubPublicStandingsView.as_view(), name="club-public-standings"),
]

