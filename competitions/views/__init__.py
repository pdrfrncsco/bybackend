from competitions.views.competition_views import (
    CompetitionListCreateView,
    CompetitionDetailView,
    CompetitionConfigView,
)
from competitions.views.v2_views import (
    CompetitionRegisterClubView,
    CompetitionGenerateScheduleView,
    CompetitionMatchListView,
    MatchDetailView,
    MatchScoreUpdateView,
    CompetitionStandingListView,
    CompetitionBracketView,
    CompetitionRoundsView,
    CompetitionDrawView,
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
    "MatchDetailView",
    "MatchScoreUpdateView",
    "CompetitionStandingListView",
    "CompetitionBracketView",
    "CompetitionRoundsView",
    "CompetitionDrawView",
    "CompetitionRegulationListCreateView",
    "CompetitionRegulationDetailView",
    "LineupSubmissionViewSet",
    "MatchReportViewSet",
]
