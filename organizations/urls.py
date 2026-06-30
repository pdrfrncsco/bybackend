"""
BOLAYETU — Organizations URL Configuration

All organization endpoints are under /api/v1/organizations/.
"""

from django.urls import path

from organizations.views import (
    OrganizationMeView,
    OrganizationLogoView,
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
)

urlpatterns = [
    # Authenticated — Organization Management
    path("me/", OrganizationMeView.as_view(), name="organization-me"),
    path("me/logo/", OrganizationLogoView.as_view(), name="organization-logo"),
    path("me/launch/", OrganizationLaunchView.as_view(), name="organization-launch"),
    path("me/onboarding-status/", OrganizationOnboardingStatusView.as_view(), name="organization-onboarding-status"),

    # Public — Organization Discovery
    path("public/", OrganizationPublicListView.as_view(), name="organization-public-list"),
    path("public/<slug:slug>/", OrganizationPublicDetailView.as_view(), name="organization-public-detail"),
    path("public/<slug:slug>/kpis/", OrganizationKpisView.as_view(), name="organization-kpis"),
    path("public/<slug:slug>/history/", OrganizationHistoryView.as_view(), name="organization-history"),
    path("public/<slug:slug>/tournaments/", OrganizationTournamentsView.as_view(), name="organization-tournaments"),
    path("public/<slug:slug>/clubs/", OrganizationClubsView.as_view(), name="organization-clubs"),

    # Authenticated — Subscriptions
    path("public/<slug:slug>/subscribe/", OrganizationSubscribeView.as_view(), name="organization-subscribe"),
    path("public/<slug:slug>/unsubscribe/", OrganizationUnsubscribeView.as_view(), name="organization-unsubscribe"),
]
