"""
BOLAYETU — Fans App API Views
"""

from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import FollowTargetType
from .selectors import FanSelector
from .serializers import (
    FanProfileSerializer,
    FanProfileUpdateSerializer,
    FanFollowSerializer,
    ToggleFollowInputSerializer,
    MatchPredictionSerializer,
    SubmitPredictionInputSerializer,
    FanLeaderboardSerializer,
    FanMVPVoteInputSerializer,
)
from .services import (
    FanProfileService,
    FanFollowService,
    MatchPredictionService,
    FanMVPVoteService,
)


class FanProfileMeView(APIView):
    """
    Retrieve or update current authenticated user's Fan Profile.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get My Fan Profile",
        responses={200: FanProfileSerializer},
        tags=["Fans"],
    )
    def get(self, request):
        profile = FanProfileService.get_or_create_profile(request.user)
        serializer = FanProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Update My Fan Profile",
        request=FanProfileUpdateSerializer,
        responses={200: FanProfileSerializer},
        tags=["Fans"],
    )
    def patch(self, request):
        serializer = FanProfileUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_profile = FanProfileService.update_profile(request.user, **serializer.validated_data)
        return Response(FanProfileSerializer(updated_profile).data, status=status.HTTP_200_OK)


class FanFollowsView(APIView):
    """
    List followed clubs, players, and competitions.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List Followed Entities",
        parameters=[
            OpenApiParameter(
                name="type",
                type=str,
                enum=["club", "player", "competition"],
                description="Filter by target type",
                required=False,
            )
        ],
        responses={200: FanFollowSerializer(many=True)},
        tags=["Fans"],
    )
    def get(self, request):
        target_type = request.query_params.get("type")
        follows = FanSelector.get_user_follows(request.user, target_type=target_type)
        serializer = FanFollowSerializer(follows, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class FanToggleFollowView(APIView):
    """
    Toggle follow state on a club, player, or competition.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Toggle Follow",
        request=ToggleFollowInputSerializer,
        responses={200: FanFollowSerializer},
        tags=["Fans"],
    )
    def post(self, request):
        serializer = ToggleFollowInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        target_type = serializer.validated_data["target_type"]
        target_id = serializer.validated_data["target_id"]

        follow, is_following = FanFollowService.toggle_follow(
            user=request.user,
            target_type=target_type,
            target_id=target_id,
        )

        return Response(
            {
                "is_following": is_following,
                "target_type": target_type,
                "target_id": str(target_id),
                "follow": FanFollowSerializer(follow).data if follow else None,
            },
            status=status.HTTP_200_OK,
        )


class FanPredictionsView(APIView):
    """
    List user predictions or submit a new match score prediction.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List My Predictions",
        responses={200: MatchPredictionSerializer(many=True)},
        tags=["Fans"],
    )
    def get(self, request):
        predictions = FanSelector.get_user_predictions(request.user)
        serializer = MatchPredictionSerializer(predictions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Submit Match Prediction",
        request=SubmitPredictionInputSerializer,
        responses={201: MatchPredictionSerializer},
        tags=["Fans"],
    )
    def post(self, request):
        serializer = SubmitPredictionInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        match_id = serializer.validated_data["match_id"]
        home_score = serializer.validated_data["predicted_home_score"]
        away_score = serializer.validated_data["predicted_away_score"]

        prediction = MatchPredictionService.submit_prediction(
            user=request.user,
            match_id=match_id,
            home_score=home_score,
            away_score=away_score,
        )

        return Response(MatchPredictionSerializer(prediction).data, status=status.HTTP_201_CREATED)


class FanLeaderboardView(APIView):
    """
    Monthly Prediction League Leaderboard.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Prediction League Leaderboard",
        responses={200: FanLeaderboardSerializer(many=True)},
        tags=["Fans"],
    )
    def get(self, request):
        profiles = list(FanSelector.get_leaderboard(limit=50))
        # Annotate 1-based ranks
        for idx, p in enumerate(profiles, start=1):
            p.rank = idx

        serializer = FanLeaderboardSerializer(profiles, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class FanMVPVoteView(APIView):
    """
    Vote for Match MVP.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Vote for Match MVP",
        request=FanMVPVoteInputSerializer,
        responses={200: {"message": "Vote registered"}},
        tags=["Fans"],
    )
    def post(self, request):
        serializer = FanMVPVoteInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        match_id = serializer.validated_data["match_id"]
        player_id = serializer.validated_data["player_id"]

        FanMVPVoteService.cast_vote(
            user=request.user,
            match_id=match_id,
            player_id=player_id,
        )

        return Response(
            {"detail": "Voto para Homem do Jogo registado com sucesso!"},
            status=status.HTTP_200_OK,
        )
