"""
BOLAYETU — Players URL Configuration

Public API for players (global domain).

Endpoints:
    GET    /api/v1/players/              — List players
    POST   /api/v1/players/              — Create player (staff only)
    GET    /api/v1/players/search/       — Search players
    GET    /api/v1/players/{slug}/       — Get player detail
    PATCH  /api/v1/players/{slug}/       — Update player (staff only)
    POST   /api/v1/players/{slug}/register/ — Register player at a club
    
    GET    /api/v1/players/{slug}/documents/     — List player documents
    POST   /api/v1/players/{slug}/documents/     — Upload document (staff only)
    GET    /api/v1/players/{slug}/documents/{id}/ — Get document detail
    PATCH  /api/v1/players/{slug}/documents/{id}/ — Update document (staff only)
    DELETE /api/v1/players/{slug}/documents/{id}/ — Delete document (staff only)
    POST   /api/v1/players/{slug}/documents/{id}/verify/ — Verify document (admin only)
    
    GET    /api/v1/players/{slug}/videos/        — List player videos
    POST   /api/v1/players/{slug}/videos/        — Upload video (staff only)
    GET    /api/v1/players/{slug}/videos/{id}/    — Get video detail
    PATCH  /api/v1/players/{slug}/videos/{id}/    — Update video (staff only)
    DELETE /api/v1/players/{slug}/videos/{id}/    — Delete video (staff only)
    POST   /api/v1/players/{slug}/videos/{id}/publish/ — Publish video (staff only)
    
    GET    /api/v1/players/{slug}/achievements/      — List player achievements
    POST   /api/v1/players/{slug}/achievements/      — Add achievement (staff only)
    GET    /api/v1/players/{slug}/achievements/{id}/  — Get achievement detail
    PATCH  /api/v1/players/{slug}/achievements/{id}/  — Update achievement (staff only)
    DELETE /api/v1/players/{slug}/achievements/{id}/  — Delete achievement (staff only)
    POST   /api/v1/players/{slug}/achievements/{id}/verify/ — Verify achievement (admin only)
"""

from django.urls import path

from players.views import (
    PlayerListCreateView,
    PlayerDetailUpdateView,
    PlayerSearchView,
    PlayerRegisterView,
)
from players.views.player_me_views import PlayerAvatarView, PlayerMeView, PlayerOnboardingStatusView
from players.views.player_onboarding_views import PlayerOnboardingCompleteStepView
from players.views.player_registration_request_views import PlayerMeRegistrationRequestListCreateView
from players.views.player_document_views import (
    PlayerDocumentListView,
    PlayerDocumentDetailView,
    PlayerDocumentVerifyView,
)
from players.views.player_video_views import (
    PlayerVideoListView,
    PlayerVideoDetailView,
    PlayerVideoPublishView,
)
from players.views.player_achievement_views import (
    PlayerAchievementListView,
    PlayerAchievementDetailView,
    PlayerAchievementVerifyView,
)
from players.views.player_identity_views import (
    PlayerIdentityDocumentListView,
    PlayerIdentityDocumentDetailView,
    PlayerIdentityDocumentVerifyView,
)
from players.views.player_contact_views import (
    PlayerContactView,
    PlayerEmergencyContactListCreateView,
)
from players.views.player_career_views import PlayerCareerListView
from players.views.player_statistics_views import PlayerStatisticsListView
from players.views.player_football_profile_views import PlayerFootballProfileView
from players.views.player_invite_views import InvitePlayerView, RedeemInviteView

urlpatterns = [
    # Player CRUD
    path("", PlayerListCreateView.as_view(), name="player-list-create"),
    path("search/", PlayerSearchView.as_view(), name="player-search"),
    path("me/", PlayerMeView.as_view(), name="player-me"),
    path("me/onboarding-status/", PlayerOnboardingStatusView.as_view(), name="player-onboarding-status"),
    path("me/onboarding/complete-step/", PlayerOnboardingCompleteStepView.as_view(), name="player-onboarding-complete-step"),
    path("me/avatar/", PlayerAvatarView.as_view(), name="player-me-avatar"),
    path("me/registration-requests/", PlayerMeRegistrationRequestListCreateView.as_view(), name="player-me-registration-requests"),
    path("<slug:slug>/", PlayerDetailUpdateView.as_view(), name="player-detail-update"),
    path("<slug:slug>/avatar/", PlayerAvatarView.as_view(), name="player-avatar"),
    path("<slug:slug>/register/", PlayerRegisterView.as_view(), name="player-register"),
    
    # Player Documents
    path(
        "<slug:slug>/documents/",
        PlayerDocumentListView.as_view(),
        name="player-document-list",
    ),
    path(
        "<slug:slug>/documents/<uuid:document_id>/",
        PlayerDocumentDetailView.as_view(),
        name="player-document-detail",
    ),
    path(
        "<slug:slug>/documents/<uuid:document_id>/verify/",
        PlayerDocumentVerifyView.as_view(),
        name="player-document-verify",
    ),
    
    # Player Videos
    path(
        "<slug:slug>/videos/",
        PlayerVideoListView.as_view(),
        name="player-video-list",
    ),
    path(
        "<slug:slug>/videos/<uuid:video_id>/",
        PlayerVideoDetailView.as_view(),
        name="player-video-detail",
    ),
    path(
        "<slug:slug>/videos/<uuid:video_id>/publish/",
        PlayerVideoPublishView.as_view(),
        name="player-video-publish",
    ),
    
    # Player Achievements
    path(
        "<slug:slug>/achievements/",
        PlayerAchievementListView.as_view(),
        name="player-achievement-list",
    ),
    path(
        "<slug:slug>/achievements/<uuid:achievement_id>/",
        PlayerAchievementDetailView.as_view(),
        name="player-achievement-detail",
    ),
    path(
        "<slug:slug>/achievements/<uuid:achievement_id>/verify/",
        PlayerAchievementVerifyView.as_view(),
        name="player-achievement-verify",
    ),

    # Phase 1: Identity & Contact endpoints
    path(
        "<slug:slug>/identity-documents/",
        PlayerIdentityDocumentListView.as_view(),
        name="player-identity-document-list",
    ),
    path(
        "<slug:slug>/identity-documents/<uuid:document_id>/",
        PlayerIdentityDocumentDetailView.as_view(),
        name="player-identity-document-detail",
    ),
    path(
        "<slug:slug>/identity-documents/<uuid:document_id>/verify/",
        PlayerIdentityDocumentVerifyView.as_view(),
        name="player-identity-document-verify",
    ),

    path(
        "<slug:slug>/contact/",
        PlayerContactView.as_view(),
        name="player-contact",
    ),
    path(
        "<slug:slug>/emergency-contacts/",
        PlayerEmergencyContactListCreateView.as_view(),
        name="player-emergency-contact-list-create",
    ),
    # Invite endpoint (admin)
    path(
        "invite/",
        InvitePlayerView.as_view(),
        name="player-invite",
    ),
    path(
        "invite/redeem/",
        RedeemInviteView.as_view(),
        name="player-invite-redeem",
    ),
    # Phase 2: Career timeline
    path(
        "<slug:slug>/career/",
        PlayerCareerListView.as_view(),
        name="player-career-list",
    ),
    # Football profile (Phase 2)
    path(
        "<slug:slug>/football-profile/",
        PlayerFootballProfileView.as_view(),
        name="player-football-profile",
    ),
    # Season statistics
    path(
        "<slug:slug>/statistics/",
        PlayerStatisticsListView.as_view(),
        name="player-statistics-list",
    ),
    path(
        "<slug:slug>/statistics/<str:season>/",
        PlayerStatisticsListView.as_view(),
        name="player-statistics-season",
    ),
]
