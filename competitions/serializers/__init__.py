from competitions.serializers.competition import (
    CompetitionSerializer,
    CompetitionCreateSerializer,
    CompetitionUpdateSerializer,
    CompetitionConfigSerializer,
)
from competitions.serializers.v2_serializers import (
    CompetitionRegistrationSerializer,
    MatchSerializer,
    StandingSerializer,
)
from competitions.serializers.regulation import (
    CompetitionRegulationSerializer,
    CompetitionRegulationCreateSerializer,
    CompetitionRegulationUpdateSerializer,
)
from competitions.serializers.fair_play_serializers import (
    PlayerSuspensionSerializer,
    CreateSuspensionSerializer,
    CompetitionRankingSerializer,
    PlayerEligibilitySerializer,
    FairPlayRankingSerializer,
    TopScorerSerializer,
)
from competitions.serializers.lineup_serializers import (
    LineupSubmissionSerializer,
    LineupSubmissionInputSerializer,
    LineupSubmissionDetailSerializer,
    MatchLineupPlayerSerializer,
    MatchReportSerializer,
    MatchReportInputSerializer,
    GoalInputSerializer,
    GoalSerializer,
    MatchStatsSerializer,
    PlayerBasicSerializer,
)

__all__ = [
    "CompetitionSerializer",
    "CompetitionCreateSerializer",
    "CompetitionUpdateSerializer",
    "CompetitionConfigSerializer",
    "CompetitionRegistrationSerializer",
    "MatchSerializer",
    "StandingSerializer",
    "CompetitionRegulationSerializer",
    "CompetitionRegulationCreateSerializer",
    "CompetitionRegulationUpdateSerializer",
    "PlayerSuspensionSerializer",
    "CreateSuspensionSerializer",
    "CompetitionRankingSerializer",
    "PlayerEligibilitySerializer",
    "FairPlayRankingSerializer",
    "TopScorerSerializer",
    "LineupSubmissionSerializer",
    "LineupSubmissionInputSerializer",
    "LineupSubmissionDetailSerializer",
    "MatchLineupPlayerSerializer",
    "MatchReportSerializer",
    "MatchReportInputSerializer",
    "GoalInputSerializer",
    "GoalSerializer",
    "MatchStatsSerializer",
    "PlayerBasicSerializer",
]
