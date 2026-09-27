"""
BOLAYETU — Fans App API Views
"""

from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied, NotFound

from .models import FollowTargetType, FeedPost
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
    FeedPostSerializer,
    FeedPostCreateSerializer,
    FeedPostCommentSerializer,
)
from .services import (
    FanProfileService,
    FanFollowService,
    MatchPredictionService,
    FanMVPVoteService,
    FeedPostService,
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


# ─────────────────────────────────────────────────────────────────────
# CONTENT PUBLISHING VIEWS ("PUBLICAR NO FEED")
# ─────────────────────────────────────────────────────────────────────

class FeedPostsView(APIView):
    """
    List feed posts or publish a new post (for Organizations, Clubs, Players).
    """

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    @extend_schema(
        summary="List Feed Posts",
        parameters=[
            OpenApiParameter(name="category", type=str, required=False),
            OpenApiParameter(name="author_type", type=str, required=False),
            OpenApiParameter(name="club_id", type=str, required=False),
            OpenApiParameter(name="player_id", type=str, required=False),
            OpenApiParameter(name="organization_id", type=str, required=False),
        ],
        responses={200: FeedPostSerializer(many=True)},
        tags=["Feed & Social"],
    )
    def get(self, request):
        category = request.query_params.get("category")
        author_type = request.query_params.get("author_type")
        club_id = request.query_params.get("club_id")
        player_id = request.query_params.get("player_id")
        org_id = request.query_params.get("organization_id")

        posts = FanSelector.get_feed_posts(
            user=request.user if request.user.is_authenticated else None,
            category=category,
            author_type=author_type,
            club_id=club_id,
            player_id=player_id,
            organization_id=org_id,
        )
        serializer = FeedPostSerializer(posts, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Publish Post to Feed",
        request=FeedPostCreateSerializer,
        responses={201: FeedPostSerializer},
        tags=["Feed & Social"],
    )
    def post(self, request):
        serializer = FeedPostCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        post = FeedPostService.create_post(
            user=request.user,
            **serializer.validated_data,
        )
        response_serializer = FeedPostSerializer(post, context={"request": request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class FeedPostDetailView(APIView):
    """
    Retrieve or delete a single feed post.
    """

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    @extend_schema(
        summary="Get Feed Post Details",
        responses={200: FeedPostSerializer},
        tags=["Feed & Social"],
    )
    def get(self, request, post_id):
        post = FeedPost.objects.filter(id=post_id).select_related(
            "author_user", "club", "player", "organization"
        ).first()
        if not post:
            raise NotFound("Publicação não encontrada.")
        serializer = FeedPostSerializer(post, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Delete Feed Post",
        responses={204: None},
        tags=["Feed & Social"],
    )
    def delete(self, request, post_id):
        post = FeedPost.objects.filter(id=post_id).first()
        if not post:
            raise NotFound("Publicação não encontrada.")

        # Check ownership or admin
        if post.author_user != request.user and not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied("Não tem permissão para eliminar esta publicação.")

        post.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FeedPostToggleLikeView(APIView):
    """
    Like or unlike a feed post.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Toggle Like on Feed Post",
        responses={200: {"is_liked": True, "likes_count": 42}},
        tags=["Feed & Social"],
    )
    def post(self, request, post_id):
        post, is_liked = FeedPostService.toggle_like(user=request.user, post_id=post_id)
        return Response(
            {
                "is_liked": is_liked,
                "likes_count": post.likes_count,
            },
            status=status.HTTP_200_OK,
        )


class FeedPostCommentsView(APIView):
    """
    List or add comments on a feed post.
    """

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    @extend_schema(
        summary="List Feed Post Comments",
        responses={200: FeedPostCommentSerializer(many=True)},
        tags=["Feed & Social"],
    )
    def get(self, request, post_id):
        comments = FanSelector.get_post_comments(post_id=post_id)
        serializer = FeedPostCommentSerializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Add Comment to Feed Post",
        request={"application/json": {"type": "object", "properties": {"content": {"type": "string"}}, "required": ["content"]}},
        responses={201: FeedPostCommentSerializer},
        tags=["Feed & Social"],
    )
    def post(self, request, post_id):
        content = request.data.get("content", "")
        comment = FeedPostService.add_comment(user=request.user, post_id=post_id, content=content)
        serializer = FeedPostCommentSerializer(comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
