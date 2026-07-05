from competitions.views.competition_views import (
    CompetitionListCreateView,
    CompetitionDetailView,
)
from competitions.views.v2_views import (
    CompetitionRegisterClubView,
    CompetitionGenerateScheduleView,
    CompetitionMatchListView,
    MatchScoreUpdateView,
    CompetitionStandingListView,
)
from competitions.views.regulation_views import (
    CompetitionRegulationListCreateView,
    CompetitionRegulationDetailView,
)
from competitions.views.lineup_views import (
    LineupSubmissionViewSet,
    MatchReportViewSet,
)

__all__ = [
    "CompetitionListCreateView",
    "CompetitionDetailView",
    "CompetitionRegisterClubView",
    "CompetitionGenerateScheduleView",
    "CompetitionMatchListView",
    "MatchScoreUpdateView",
    "CompetitionStandingListView",
    "CompetitionRegulationListCreateView",
    "CompetitionRegulationDetailView",
    "LineupSubmissionViewSet",
    "MatchReportViewSet",
]
