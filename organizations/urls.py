"""
BOLAYETU — Organizations URL Configuration

All organization endpoints are under /api/v1/organizations/.
"""

from django.urls import path

from organizations.views import (
    OrganizationMeView,
    OrganizationLogoView,
    OrganizationBannerView,
    OrganizationLaunchView,
    OrganizationOnboardingStatusView,
    OrganizationPublicListView,
    OrganizationPublicDetailView,
    OrganizationKpisView,
    OrganizationHistoryView,
    OrganizationTournamentsView,
    OrganizationClubsView,
    OrganizationSubscribeView,
    OrganizationUnsubscribeView,
    OrganizationMembersView,
    OrganizationMemberDetailView,
    OrganizationClubRequestCreateView,
    OrganizationClubRequestsView,
    OrganizationClubRequestReviewView,
)

urlpatterns = [
    # Authenticated — Organization Management
    path("me/", OrganizationMeView.as_view(), name="organization-me"),
    path("me/logo/", OrganizationLogoView.as_view(), name="organization-logo"),
    path("me/banner/", OrganizationBannerView.as_view(), name="organization-banner"),
    path("me/launch/", OrganizationLaunchView.as_view(), name="organization-launch"),
    path("me/onboarding-status/", OrganizationOnboardingStatusView.as_view(), name="organization-onboarding-status"),
    path("me/members/", OrganizationMembersView.as_view(), name="organization-members"),
    path("me/members/<uuid:membership_id>/", OrganizationMemberDetailView.as_view(), name="organization-member-detail"),

    # Public — Organization Discovery
    path("public/", OrganizationPublicListView.as_view(), name="organization-public-list"),
    path("public/<slug:slug>/", OrganizationPublicDetailView.as_view(), name="organization-public-detail"),
    path("public/<slug:slug>/kpis/", OrganizationKpisView.as_view(), name="organization-kpis"),
    path("public/<slug:slug>/history/", OrganizationHistoryView.as_view(), name="organization-history"),
    path("public/<slug:slug>/tournaments/", OrganizationTournamentsView.as_view(), name="organization-tournaments"),
    path("public/<slug:slug>/clubs/", OrganizationClubsView.as_view(), name="organization-clubs"),
    path("public/<slug:slug>/club-requests/", OrganizationClubRequestCreateView.as_view(), name="organization-club-request-create"),

    # Authenticated — Subscriptions
    path("public/<slug:slug>/subscribe/", OrganizationSubscribeView.as_view(), name="organization-subscribe"),
    path("public/<slug:slug>/unsubscribe/", OrganizationUnsubscribeView.as_view(), name="organization-unsubscribe"),

    # Authenticated — Club request management
    path("me/club-requests/", OrganizationClubRequestsView.as_view(), name="organization-club-requests"),
    path("me/club-requests/<uuid:request_id>/", OrganizationClubRequestReviewView.as_view(), name="organization-club-request-review"),
]
