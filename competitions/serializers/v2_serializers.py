"""
BOLAYETU — v2 Serializers

Serializers for CompetitionRegistrations, Matches, and Standings.
"""

from rest_framework import serializers

from clubs.models import Club
from competitions.models import CompetitionRegistration, Match, Standing


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
        return obj.club.logo.url if obj.club.logo else None


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
        return obj.home_club.logo.url if obj.home_club.logo else None

    def get_away_club_logo(self, obj: Match) -> str | None:
        return obj.away_club.logo.url if obj.away_club.logo else None


class StandingSerializer(serializers.ModelSerializer):
    club_name = serializers.CharField(source="club.name", read_only=True)
    club_logo = serializers.SerializerMethodField()

    class Meta:
        model = Standing
        fields = [
            "id",
            "competition",
            "club",
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
        return obj.club.logo.url if obj.club.logo else None
