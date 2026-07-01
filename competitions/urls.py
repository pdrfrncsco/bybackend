from django.urls import path

from competitions.views import (
    CompetitionListCreateView,
    CompetitionDetailView,
    CompetitionRegisterClubView,
    CompetitionGenerateScheduleView,
    CompetitionMatchListView,
    MatchScoreUpdateView,
    CompetitionStandingListView,
)
from competitions.views.match_center_views import (
    MatchEventListCreateView,
    MatchEventDeleteView,
    CompetitionPlayerStatsView,
)

urlpatterns = [
    # Competition CRUD
    path("", CompetitionListCreateView.as_view(), name="competition-list-create"),
    path("<uuid:competition_id>/", CompetitionDetailView.as_view(), name="competition-detail"),

    # Phase 3 — Registration, Schedule, Matches, Standings
    path("<uuid:competition_id>/register-club/", CompetitionRegisterClubView.as_view(), name="competition-register-club"),
    path("<uuid:competition_id>/generate-schedule/", CompetitionGenerateScheduleView.as_view(), name="competition-generate-schedule"),
    path("<uuid:competition_id>/matches/", CompetitionMatchListView.as_view(), name="competition-match-list"),
    path("<uuid:competition_id>/standings/", CompetitionStandingListView.as_view(), name="competition-standing-list"),
    path("matches/<uuid:match_id>/", MatchScoreUpdateView.as_view(), name="match-score-update"),

    # Phase 4 — Match Center (súmula + player stats)
    path("<uuid:competition_id>/matches/<uuid:match_id>/events/", MatchEventListCreateView.as_view(), name="match-event-list-create"),
    path("<uuid:competition_id>/matches/<uuid:match_id>/events/<uuid:event_id>/", MatchEventDeleteView.as_view(), name="match-event-delete"),
    path("<uuid:competition_id>/stats/", CompetitionPlayerStatsView.as_view(), name="competition-player-stats"),
]
