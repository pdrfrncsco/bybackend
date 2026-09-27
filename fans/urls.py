"""
BOLAYETU — Fans App URLs
"""

from django.urls import path
from .views import (
    FanProfileMeView,
    FanFollowsView,
    FanToggleFollowView,
    FanPredictionsView,
    FanLeaderboardView,
    FanMVPVoteView,
)

app_name = "fans"

urlpatterns = [
    path("me/", FanProfileMeView.as_view(), name="fan-profile-me"),
    path("follows/", FanFollowsView.as_view(), name="fan-follows-list"),
    path("follows/toggle/", FanToggleFollowView.as_view(), name="fan-toggle-follow"),
    path("predictions/", FanPredictionsView.as_view(), name="fan-predictions"),
    path("leaderboard/", FanLeaderboardView.as_view(), name="fan-leaderboard"),
    path("mvp-vote/", FanMVPVoteView.as_view(), name="fan-mvp-vote"),
]
