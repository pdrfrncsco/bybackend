from django.urls import path

from competitions.views import (
    CompetitionListCreateView,
    CompetitionDetailView,
    CompetitionRegisterClubView,
    CompetitionGenerateScheduleView,
    CompetitionMatchListView,
    MatchScoreUpdateView,
    CompetitionStandingListView,
    CompetitionRegulationListCreateView,
    CompetitionRegulationDetailView,
)
from competitions.views.match_center_views import (
    MatchEventListCreateView,
    MatchEventDeleteView,
    CompetitionPlayerStatsView,
)
from competitions.views.fair_play_views import (
    CompetitionSuspensionListView,
    PlayerEligibilityView,
    PlayerSuspensionCancelView,
    CompetitionFairPlayRankingView,
    TopScorersRankingView,
    SeasonRankingView,
    RecalculateRankingsView,
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
    path("<uuid:competition_id>/regulations/", CompetitionRegulationListCreateView.as_view(), name="competition-regulation-list-create"),
    path("<uuid:competition_id>/regulations/<uuid:regulation_id>/", CompetitionRegulationDetailView.as_view(), name="competition-regulation-detail"),
    path("matches/<uuid:match_id>/", MatchScoreUpdateView.as_view(), name="match-score-update"),

    # Phase 4 — Match Center (súmula + player stats)
    path("<uuid:competition_id>/matches/<uuid:match_id>/events/", MatchEventListCreateView.as_view(), name="match-event-list-create"),
    path("<uuid:competition_id>/matches/<uuid:match_id>/events/<uuid:event_id>/", MatchEventDeleteView.as_view(), name="match-event-delete"),
    path("<uuid:competition_id>/stats/", CompetitionPlayerStatsView.as_view(), name="competition-player-stats"),

    # Phase 2.4 — Fair Play & Suspensions
    path("<uuid:competition_id>/suspensions/", CompetitionSuspensionListView.as_view(), name="competition-suspensions"),
    path("<uuid:competition_id>/eligibility/<uuid:player_id>/", PlayerEligibilityView.as_view(), name="player-eligibility"),
    path("suspensions/<uuid:suspension_id>/cancel/", PlayerSuspensionCancelView.as_view(), name="suspension-cancel"),
    path("<uuid:competition_id>/fair-play-ranking/", CompetitionFairPlayRankingView.as_view(), name="fair-play-ranking"),

    # Phase 2.4 — Rankings
    path("rankings/top-scorers/", TopScorersRankingView.as_view(), name="top-scorers-ranking"),
    path("rankings/season/", SeasonRankingView.as_view(), name="season-ranking"),
    path("rankings/recalculate/", RecalculateRankingsView.as_view(), name="recalculate-rankings"),
]
