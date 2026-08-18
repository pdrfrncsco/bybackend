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
    competition_id = serializers.SerializerMethodField()
    round_label = serializers.SerializerMethodField()
    home_team_id = serializers.SerializerMethodField()
    home_team_name = serializers.SerializerMethodField()
    home_team_logo = serializers.SerializerMethodField()
    away_team_id = serializers.SerializerMethodField()
    away_team_name = serializers.SerializerMethodField()
    away_team_logo = serializers.SerializerMethodField()
    scheduled_at = serializers.DateTimeField(source="match_date", read_only=True)
    home_club_name = serializers.CharField(source="home_club.name", read_only=True)
    away_club_name = serializers.CharField(source="away_club.name", read_only=True)
    home_club_logo = serializers.SerializerMethodField()
    away_club_logo = serializers.SerializerMethodField()
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    current_period_label = serializers.CharField(source="get_current_period_display", read_only=True, allow_null=True)

    class Meta:
        model = Match
        fields = [
            "id",
            "competition",
            "competition_id",
            "round_number",
            "round_name",
            "round_label",
            "phase",
            "group_id",
            "home_club",
            "home_team_id",
            "home_club_name",
            "home_team_name",
            "home_club_logo",
            "home_team_logo",
            "away_club",
            "away_team_id",
            "away_club_name",
            "away_team_name",
            "away_club_logo",
            "away_team_logo",
            "match_date",
            "scheduled_at",
            "status",
            "status_label",
            "current_period",
            "current_period_label",
            "current_minute",
            "home_score",
            "away_score",
            "venue",
        ]
        read_only_fields = [
            "id",
            "competition_id",
            "home_club_name",
            "home_team_name",
            "home_club_logo",
            "home_team_logo",
            "away_club_name",
            "away_team_name",
            "away_club_logo",
            "away_team_logo",
            "status_label",
            "current_period_label",
            "scheduled_at",
            "round_label",
        ]

    def get_competition_id(self, obj: Match) -> str:
        return str(obj.competition_id)

    def get_round_label(self, obj: Match) -> str | None:
        return obj.round_name

    def get_home_team_id(self, obj: Match) -> str:
        return str(obj.home_club_id)

    def get_home_team_name(self, obj: Match) -> str:
        return obj.home_club.name

    def get_home_team_logo(self, obj: Match) -> str | None:
        return get_club_logo_url(obj.home_club)

    def get_away_team_id(self, obj: Match) -> str:
        return str(obj.away_club_id)

    def get_away_team_name(self, obj: Match) -> str:
        return obj.away_club.name

    def get_away_team_logo(self, obj: Match) -> str | None:
        return get_club_logo_url(obj.away_club)

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
