from competitions.views.competition_views import (
    CompetitionListCreateView,
    CompetitionDetailView,
    CompetitionConfigView,
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
    "CompetitionConfigView",
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
