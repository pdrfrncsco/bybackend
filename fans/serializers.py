"""
BOLAYETU — Fans App Serializers
"""

from rest_framework import serializers
from .models import FanProfile, FanFollow, MatchPrediction, FanMVPVote, FollowTargetType


class FanProfileSerializer(serializers.ModelSerializer):
    """Full fan profile details."""

    email = serializers.EmailField(source="user.email", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    favorite_club_name = serializers.CharField(source="favorite_club.name", read_only=True, allow_null=True)
    favorite_club_logo = serializers.CharField(source="favorite_club.logo.url", read_only=True, allow_null=True, default=None)

    class Meta:
        model = FanProfile
        fields = [
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "favorite_club",
            "favorite_club_name",
            "favorite_club_logo",
            "bio",
            "location",
            "notification_match_start",
            "notification_goals",
            "notification_transfers",
            "points",
            "correct_predictions_count",
            "total_predictions_count",
            "badges",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "points",
            "correct_predictions_count",
            "total_predictions_count",
            "badges",
            "created_at",
            "updated_at",
        ]


class FanProfileUpdateSerializer(serializers.ModelSerializer):
    """Update fan preferences and profile."""

    class Meta:
        model = FanProfile
        fields = [
            "favorite_club",
            "bio",
            "location",
            "notification_match_start",
            "notification_goals",
            "notification_transfers",
        ]


class FanFollowSerializer(serializers.ModelSerializer):
    """Followed entity representation for frontend feed."""

    name = serializers.SerializerMethodField()
    slug = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    subtitle = serializers.SerializerMethodField()
    target_id = serializers.SerializerMethodField()

    class Meta:
        model = FanFollow
        fields = [
            "id",
            "target_type",
            "target_id",
            "name",
            "slug",
            "avatar_url",
            "subtitle",
            "created_at",
        ]

    def get_target_id(self, obj: FanFollow) -> str:
        if obj.club_id:
            return str(obj.club_id)
        if obj.player_id:
            return str(obj.player_id)
        if obj.competition_id:
            return str(obj.competition_id)
        return ""

    def get_name(self, obj: FanFollow) -> str:
        if obj.club:
            return obj.club.name
        if obj.player:
            return obj.player.full_name
        if obj.competition:
            return obj.competition.name
        return ""

    def get_slug(self, obj: FanFollow) -> str:
        if obj.club:
            return getattr(obj.club, "slug", str(obj.club.id))
        if obj.player:
            return getattr(obj.player, "slug", str(obj.player.id))
        if obj.competition:
            return getattr(obj.competition, "slug", str(obj.competition.id))
        return ""

    def get_avatar_url(self, obj: FanFollow) -> str | None:
        if obj.club and hasattr(obj.club, "logo") and obj.club.logo:
            return obj.club.logo.url
        if obj.player and hasattr(obj.player, "avatar") and obj.player.avatar:
            return obj.player.avatar.url
        return None

    def get_subtitle(self, obj: FanFollow) -> str:
        if obj.club:
            return getattr(obj.club, "city", "Clube Oficial")
        if obj.player:
            return getattr(obj.player, "primary_position", "Atleta")
        if obj.competition:
            return getattr(obj.competition, "category", "Competição")
        return ""


class ToggleFollowInputSerializer(serializers.Serializer):
    """Input payload to toggle follow state on club, player, or competition."""

    target_type = serializers.ChoiceField(choices=FollowTargetType.choices)
    target_id = serializers.UUIDField()


class MatchPredictionSerializer(serializers.ModelSerializer):
    """Match prediction details."""

    match_round = serializers.CharField(source="match.round_name", read_only=True, default="")
    competition_name = serializers.CharField(source="match.competition.name", read_only=True)
    home_team_name = serializers.CharField(source="match.home_club.name", read_only=True)
    away_team_name = serializers.CharField(source="match.away_club.name", read_only=True)
    actual_home_score = serializers.IntegerField(source="match.home_score", read_only=True, allow_null=True)
    actual_away_score = serializers.IntegerField(source="match.away_score", read_only=True, allow_null=True)

    class Meta:
        model = MatchPrediction
        fields = [
            "id",
            "match",
            "competition_name",
            "match_round",
            "home_team_name",
            "away_team_name",
            "predicted_home_score",
            "predicted_away_score",
            "actual_home_score",
            "actual_away_score",
            "status",
            "points_awarded",
            "evaluated_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "points_awarded",
            "evaluated_at",
            "created_at",
        ]


class SubmitPredictionInputSerializer(serializers.Serializer):
    """Payload to submit a match score prediction."""

    match_id = serializers.UUIDField()
    predicted_home_score = serializers.IntegerField(min_value=0, max_value=25)
    predicted_away_score = serializers.IntegerField(min_value=0, max_value=25)


class FanLeaderboardSerializer(serializers.ModelSerializer):
    """Leaderboard entry for top predicting fans."""

    username = serializers.CharField(source="user.username", read_only=True)
    full_name = serializers.SerializerMethodField()
    favorite_club_name = serializers.CharField(source="favorite_club.name", read_only=True, allow_null=True)
    rank = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = FanProfile
        fields = [
            "id",
            "username",
            "full_name",
            "favorite_club_name",
            "points",
            "correct_predictions_count",
            "total_predictions_count",
            "rank",
        ]

    def get_full_name(self, obj: FanProfile) -> str:
        name = f"{obj.user.first_name} {obj.user.last_name}".strip()
        return name or obj.user.username or "Adepto"


class FanMVPVoteInputSerializer(serializers.Serializer):
    """Payload to vote for Match MVP."""

    match_id = serializers.UUIDField()
    player_id = serializers.UUIDField()
