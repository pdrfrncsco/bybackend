"""
BOLAYETU — Clubs URL Configuration

All club endpoints are under /api/v1/clubs/.
"""

from django.urls import path

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
)

urlpatterns = [
    # Authenticated — Club Management
    path("me/", ClubMeView.as_view(), name="club-me"),
    path("me/logo/", ClubLogoView.as_view(), name="club-logo"),
    path("", ClubCreateView.as_view(), name="club-create"),

    # Authenticated — Club Status Management
    path("<slug:slug>/activate/", ClubActivateView.as_view(), name="club-activate"),
    path("<slug:slug>/suspend/", ClubSuspendView.as_view(), name="club-suspend"),

    # Authenticated — Member Management
    path("<slug:slug>/members/", ClubMembersView.as_view(), name="club-members"),
    path("<slug:slug>/members/<uuid:member_id>/", ClubMemberDetailView.as_view(), name="club-member-detail"),

    # Public — Club Discovery
    path("public/", ClubPublicListView.as_view(), name="club-public-list"),
    path("public/<slug:slug>/", ClubPublicDetailView.as_view(), name="club-public-detail"),
    path("public/<slug:slug>/kpis/", ClubKpisView.as_view(), name="club-kpis"),
    path("public/<slug:slug>/squad/", ClubSquadView.as_view(), name="club-squad"),
    path("public/<slug:slug>/staff/", ClubStaffView.as_view(), name="club-staff"),
]
