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
    FeedPostsView,
    FeedPostDetailView,
    FeedPostToggleLikeView,
    FeedPostCommentsView,
)

app_name = "fans"

urlpatterns = [
    path("me/", FanProfileMeView.as_view(), name="fan-profile-me"),
    path("follows/", FanFollowsView.as_view(), name="fan-follows-list"),
    path("follows/toggle/", FanToggleFollowView.as_view(), name="fan-toggle-follow"),
    path("predictions/", FanPredictionsView.as_view(), name="fan-predictions"),
    path("leaderboard/", FanLeaderboardView.as_view(), name="fan-leaderboard"),
    path("mvp-vote/", FanMVPVoteView.as_view(), name="fan-mvp-vote"),
    # Feed & Social Posts
    path("posts/", FeedPostsView.as_view(), name="feed-posts"),
    path("posts/<uuid:post_id>/", FeedPostDetailView.as_view(), name="feed-post-detail"),
    path("posts/<uuid:post_id>/like/", FeedPostToggleLikeView.as_view(), name="feed-post-like"),
    path("posts/<uuid:post_id>/comments/", FeedPostCommentsView.as_view(), name="feed-post-comments"),
]
