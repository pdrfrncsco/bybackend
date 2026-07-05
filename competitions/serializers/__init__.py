from competitions.serializers.competition import (
    CompetitionSerializer,
    CompetitionCreateSerializer,
    CompetitionUpdateSerializer,
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

__all__ = [
    "CompetitionSerializer",
    "CompetitionCreateSerializer",
    "CompetitionUpdateSerializer",
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
]
