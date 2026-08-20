from django.urls import path

from competitions.views import (
    CompetitionListCreateView,
    CompetitionDetailView,
    CompetitionConfigView,
    CompetitionRegisterClubView,
    CompetitionGenerateScheduleView,
    CompetitionMatchListView,
    MatchDetailView,
    MatchScoreUpdateView,
    MatchTransitionView,
    MatchClockActionView,
    CompetitionStandingListView,
    CompetitionBracketView,
    CompetitionRoundsView,
    CompetitionDrawView,
    CompetitionRegulationListCreateView,
    CompetitionRegulationDetailView,
    LineupSubmissionViewSet,
    MatchReportViewSet,
)
from competitions.views.match_center_views import (
    MatchEventListCreateView,
    MatchEventDeleteView,
    CompetitionPlayerStatsView,
    LiveMatchesView,
    MatchStreamView,
    MatchReportDocumentUploadView,
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
    path("<str:competition_id>/", CompetitionDetailView.as_view(), name="competition-detail"),
    path("<str:competition_id>/config/", CompetitionConfigView.as_view(), name="competition-config"),

    # Phase 3 — Registration, Schedule, Matches, Standings
    path("<str:competition_id>/register-club/", CompetitionRegisterClubView.as_view(), name="competition-register-club"),
    path("<str:competition_id>/generate-schedule/", CompetitionGenerateScheduleView.as_view(), name="competition-generate-schedule"),
    path("<str:competition_id>/draw/", CompetitionDrawView.as_view(), name="competition-draw"),
    path("<str:competition_id>/matches/", CompetitionMatchListView.as_view(), name="competition-match-list"),
    path("<str:competition_id>/matches/<uuid:match_id>/", MatchDetailView.as_view(), name="competition-match-detail"),
    path("<str:competition_id>/standings/", CompetitionStandingListView.as_view(), name="competition-standing-list"),
    path("<str:competition_id>/bracket/", CompetitionBracketView.as_view(), name="competition-bracket"),
    path("<str:competition_id>/rounds/", CompetitionRoundsView.as_view(), name="competition-rounds"),
    path("<str:competition_id>/regulations/", CompetitionRegulationListCreateView.as_view(), name="competition-regulation-list-create"),
    path("<str:competition_id>/regulations/<uuid:regulation_id>/", CompetitionRegulationDetailView.as_view(), name="competition-regulation-detail"),
    path("matches/<uuid:match_id>/", MatchScoreUpdateView.as_view(), name="match-score-update"),
    path("matches/<uuid:match_id>/transition/", MatchTransitionView.as_view(), name="match-transition"),
    path("matches/<uuid:match_id>/clock/action/", MatchClockActionView.as_view(), name="match-clock-action"),

    # Phase 4 — Match Center (súmula + player stats)
    path("<str:competition_id>/matches/<uuid:match_id>/events/", MatchEventListCreateView.as_view(), name="match-event-list-create"),
    path("<str:competition_id>/matches/<uuid:match_id>/events/<uuid:event_id>/", MatchEventDeleteView.as_view(), name="match-event-delete"),
    path("<str:competition_id>/stats/", CompetitionPlayerStatsView.as_view(), name="competition-player-stats"),

    # Phase 3 — Live matches (global endpoint)
    path("matches/live/", LiveMatchesView.as_view(), name="live-matches"),
    path("matches/<uuid:match_id>/stream/", MatchStreamView.as_view(), name="match-stream"),

    # Phase 2.4 — Fair Play & Suspensions
    path("<str:competition_id>/suspensions/", CompetitionSuspensionListView.as_view(), name="competition-suspensions"),
    path("<str:competition_id>/eligibility/<uuid:player_id>/", PlayerEligibilityView.as_view(), name="player-eligibility"),
    path("suspensions/<uuid:suspension_id>/cancel/", PlayerSuspensionCancelView.as_view(), name="suspension-cancel"),
    path("<str:competition_id>/fair-play-ranking/", CompetitionFairPlayRankingView.as_view(), name="fair-play-ranking"),

    # Phase 2.4 — Rankings
    path("rankings/top-scorers/", TopScorersRankingView.as_view(), name="top-scorers-ranking"),
    path("rankings/season/", SeasonRankingView.as_view(), name="season-ranking"),
    path("rankings/recalculate/", RecalculateRankingsView.as_view(), name="recalculate-rankings"),
    
    # Phase 5 — Lineups & Match Reports
    path(
        "matches/<uuid:match_id>/lineups/",
        LineupSubmissionViewSet.as_view({
            'post': 'create',
            'get': 'list'
        }),
        name="lineup-list-create"
    ),
    path(
        "matches/<uuid:match_id>/lineups/<uuid:pk>/",
        LineupSubmissionViewSet.as_view({
            'get': 'retrieve'
        }),
        name="lineup-detail"
    ),
    path(
        "matches/<uuid:match_id>/lineups/confirm/",
        LineupSubmissionViewSet.as_view({
            'post': 'confirm'
        }),
        name="lineup-confirm"
    ),
    path(
        "matches/<uuid:match_id>/lineups/lock/",
        LineupSubmissionViewSet.as_view({
            'post': 'lock'
        }),
        name="lineup-lock"
    ),
    path(
        "matches/<uuid:match_id>/report/",
        MatchReportViewSet.as_view({
            'get': 'get_report'
        }),
        name="match-report"
    ),
    path(
        "matches/<uuid:match_id>/report/create/",
        MatchReportViewSet.as_view({
            'post': 'create_report'
        }),
        name="match-report-create"
    ),
    path(
        "matches/<uuid:match_id>/report/add-goal/",
        MatchReportViewSet.as_view({
            'post': 'add_goal'
        }),
        name="match-report-add-goal"
    ),
    path(
        "matches/<uuid:match_id>/report/update-stats/",
        MatchReportViewSet.as_view({
            'post': 'update_stats'
        }),
        name="match-report-update-stats"
    ),
    # Phase 3 — Match report document upload
    path(
        "matches/<uuid:match_id>/report/document/",
        MatchReportDocumentUploadView.as_view(),
        name="match-report-document"
    ),

    # Tactical positions for a match (GET/POST)
    path(
        "matches/<uuid:match_id>/tactical_positions/",
        __import__('competitions.views.tactical_views', fromlist=['TacticalPositionsViewSet']).TacticalPositionsViewSet.as_view({'get': 'retrieve', 'post': 'create'}),
        name="tactical-positions"
    ),
]
