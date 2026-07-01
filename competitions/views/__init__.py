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

__all__ = [
    "CompetitionListCreateView",
    "CompetitionDetailView",
    "CompetitionRegisterClubView",
    "CompetitionGenerateScheduleView",
    "CompetitionMatchListView",
    "MatchScoreUpdateView",
    "CompetitionStandingListView",
]
