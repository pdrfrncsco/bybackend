"""
BOLAYETU — v2 Serializers

Serializers for CompetitionRegistrations, Matches, and Standings.
"""

from rest_framework import serializers

from competitions.models import CompetitionRegistration, Match, Standing
from competitions.serializers.utils import get_club_logo_url


class CompetitionRegistrationSerializer(serializers.ModelSerializer):
    club_name = serializers.CharField(source="club.name", read_only=True)
    club_logo = serializers.SerializerMethodField()

    class Meta:
        model = CompetitionRegistration
        fields = [
            "id",
            "competition",
            "club",
            "club_name",
            "club_logo",
            "registered_at",
        ]
    read_only_fields = ["id", "club_name", "club_logo", "registered_at"]

    def get_club_logo(self, obj: CompetitionRegistration) -> str | None:
        return get_club_logo_url(obj.club)


class MatchSerializer(serializers.ModelSerializer):
    home_club_name = serializers.CharField(source="home_club.name", read_only=True)
    away_club_name = serializers.CharField(source="away_club.name", read_only=True)
    home_club_logo = serializers.SerializerMethodField()
    away_club_logo = serializers.SerializerMethodField()
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Match
        fields = [
            "id",
            "competition",
            "round_number",
            "round_name",
            "phase",
            "group_id",
            "home_club",
            "home_club_name",
            "home_club_logo",
            "away_club",
            "away_club_name",
            "away_club_logo",
            "match_date",
            "status",
            "status_label",
            "home_score",
            "away_score",
            "venue",
        ]
        read_only_fields = [
            "id",
            "home_club_name",
            "home_club_logo",
            "away_club_name",
            "away_club_logo",
            "status_label",
        ]

    def get_home_club_logo(self, obj: Match) -> str | None:
        return get_club_logo_url(obj.home_club)

    def get_away_club_logo(self, obj: Match) -> str | None:
        return get_club_logo_url(obj.away_club)


class MatchCreateSerializer(serializers.Serializer):
    home_club = serializers.UUIDField()
    away_club = serializers.UUIDField()
    match_date = serializers.DateTimeField()
    round_number = serializers.IntegerField(required=False, min_value=1, default=1)
    round_name = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=100)
    phase = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=50)
    group_id = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=64)
    venue = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=255)
    status = serializers.ChoiceField(
        choices=Match.MatchStatus.choices,
        required=False,
        default=Match.MatchStatus.SCHEDULED,
    )

    def validate(self, attrs):
        if attrs["home_club"] == attrs["away_club"]:
            raise serializers.ValidationError("Home and away clubs must be different.")
        return attrs


class StandingSerializer(serializers.ModelSerializer):
    club_name = serializers.CharField(source="club.name", read_only=True)
    club_logo = serializers.SerializerMethodField()

    class Meta:
        model = Standing
        fields = [
            "id",
            "competition",
            "club",
            "phase",
            "group_id",
            "club_name",
            "club_logo",
            "played",
            "won",
            "drawn",
            "lost",
            "goals_for",
            "goals_against",
            "goal_difference",
            "points",
            "position",
        ]
        read_only_fields = [
            "id",
            "phase",
            "group_id",
            "club_name",
            "club_logo",
            "played",
            "won",
            "drawn",
            "lost",
            "goals_for",
            "goals_against",
            "goal_difference",
            "points",
            "position",
        ]

    def get_club_logo(self, obj: Standing) -> str | None:
        return get_club_logo_url(obj.club)
