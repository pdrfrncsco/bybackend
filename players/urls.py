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
"""

from django.urls import path

from players.views import (
    PlayerListCreateView,
    PlayerDetailUpdateView,
    PlayerSearchView,
    PlayerRegisterView,
)

urlpatterns = [
    path("", PlayerListCreateView.as_view(), name="player-list-create"),
    path("search/", PlayerSearchView.as_view(), name="player-search"),
    path("<slug:slug>/", PlayerDetailUpdateView.as_view(), name="player-detail-update"),
    path("<slug:slug>/register/", PlayerRegisterView.as_view(), name="player-register"),
]
