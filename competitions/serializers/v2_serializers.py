"""
BOLAYETU — v2 Serializers

Serializers for CompetitionRegistrations, Matches, and Standings.
"""

from django.db.models import Q
from rest_framework import serializers

from competitions.models import CompetitionRegistration, Match, Standing
from competitions.serializers.utils import get_club_logo_url


class CompetitionRegistrationSerializer(serializers.ModelSerializer):
    club_name = serializers.CharField(source="club.name", read_only=True)
    club_short_name = serializers.CharField(source="club.short_name", read_only=True, allow_null=True)
    club_acronym = serializers.CharField(source="club.acronym", read_only=True, allow_null=True)
    club_logo = serializers.SerializerMethodField()

    class Meta:
        model = CompetitionRegistration
        fields = [
            "id",
            "competition",
            "club",
            "club_name",
            "club_short_name",
            "club_acronym",
            "club_logo",
            "registered_at",
        ]
    read_only_fields = ["id", "club_name", "club_short_name", "club_acronym", "club_logo", "registered_at"]

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
    home_club_short_name = serializers.CharField(source="home_club.short_name", read_only=True, allow_null=True)
    home_club_acronym = serializers.CharField(source="home_club.acronym", read_only=True, allow_null=True)
    away_club_name = serializers.CharField(source="away_club.name", read_only=True)
    away_club_short_name = serializers.CharField(source="away_club.short_name", read_only=True, allow_null=True)
    away_club_acronym = serializers.CharField(source="away_club.acronym", read_only=True, allow_null=True)
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
            "home_club_short_name",
            "home_club_acronym",
            "home_team_name",
            "home_club_logo",
            "home_team_logo",
            "away_club",
            "away_team_id",
            "away_club_name",
            "away_club_short_name",
            "away_club_acronym",
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
            "clock_running",
            "clock_started_at",
            "clock_elapsed_seconds",
            "stoppage_time_minutes",
            "clock_version",
            "home_score",
            "away_score",
            "home_penalty_score",
            "away_penalty_score",
            "venue",
        ]
        read_only_fields = [
            "id",
            "competition_id",
            "home_club_name",
            "home_club_short_name",
            "home_club_acronym",
            "home_team_name",
            "home_club_logo",
            "home_team_logo",
            "away_club_name",
            "away_club_short_name",
            "away_club_acronym",
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


class MatchUpdateSerializer(serializers.Serializer):
    home_club = serializers.UUIDField(required=False)
    away_club = serializers.UUIDField(required=False)
    match_date = serializers.DateTimeField(required=False)
    round_number = serializers.IntegerField(required=False, min_value=1)
    round_name = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=100)
    phase = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=50)
    group_id = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=64)
    venue = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=255)
    status = serializers.ChoiceField(
        choices=Match.MatchStatus.choices,
        required=False,
    )

    def validate(self, attrs):
        home = attrs.get("home_club")
        away = attrs.get("away_club")
        if home and away and home == away:
            raise serializers.ValidationError("Home and away clubs must be different.")
        return attrs


class StandingSerializer(serializers.ModelSerializer):
    competition_name = serializers.CharField(source="competition.name", read_only=True)
    club_name = serializers.CharField(source="club.name", read_only=True)
    club_short_name = serializers.CharField(source="club.short_name", read_only=True, allow_null=True)
    club_acronym = serializers.CharField(source="club.acronym", read_only=True, allow_null=True)
    club_logo = serializers.SerializerMethodField()
    form = serializers.SerializerMethodField()

    class Meta:
        model = Standing
        fields = [
            "id",
            "competition",
            "competition_name",
            "club",
            "phase",
            "group_id",
            "club_name",
            "club_short_name",
            "club_acronym",
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
            "form",
        ]
        read_only_fields = [
            "id",
            "competition",
            "competition_name",
            "phase",
            "group_id",
            "club_name",
            "club_short_name",
            "club_acronym",
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
            "form",
        ]

    def get_club_logo(self, obj: Standing) -> str | None:
        return get_club_logo_url(obj.club)

    def get_form(self, obj: Standing) -> list[str]:
        """Returns recent form for the last 5 completed matches: ['W', 'D', 'L', ...]"""
        matches = Match.objects.filter(
            competition=obj.competition,
            tenant=obj.tenant,
            status=Match.MatchStatus.FINISHED,
        )
        if obj.group_id:
            matches = matches.filter(group_id=obj.group_id)
        if obj.phase:
            matches = matches.filter(phase=obj.phase)

        club_matches = matches.filter(
            Q(home_club=obj.club) | Q(away_club=obj.club)
        ).order_by("-match_date")[:5]

        form_list: list[str] = []
        for m in reversed(list(club_matches)):
            if m.home_score is None or m.away_score is None:
                continue
            if m.home_club_id == obj.club_id:
                if m.home_score > m.away_score:
                    form_list.append("W")
                elif m.home_score == m.away_score:
                    form_list.append("D")
                else:
                    form_list.append("L")
            else:
                if m.away_score > m.home_score:
                    form_list.append("W")
                elif m.away_score == m.home_score:
                    form_list.append("D")
                else:
                    form_list.append("L")
        return form_list


class ManualScoresheetGoalSerializer(serializers.Serializer):
    club_id = serializers.UUIDField()
    player_id = serializers.UUIDField(required=False, allow_null=True)
    assist_player_id = serializers.UUIDField(required=False, allow_null=True)
    minute = serializers.IntegerField(default=1, min_value=0, max_value=130)
    event_type = serializers.ChoiceField(
        choices=["goal", "penalty_scored", "own_goal"],
        default="goal",
    )
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class ManualScoresheetCardSerializer(serializers.Serializer):
    club_id = serializers.UUIDField()
    player_id = serializers.UUIDField(required=False, allow_null=True)
    minute = serializers.IntegerField(default=1, min_value=0, max_value=130)
    event_type = serializers.ChoiceField(
        choices=["yellow_card", "red_card", "yellow_red"],
        default="yellow_card",
    )
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class ManualScoresheetSubstitutionSerializer(serializers.Serializer):
    club_id = serializers.UUIDField()
    player_id = serializers.UUIDField(required=False, allow_null=True)
    player_off_id = serializers.UUIDField(required=False, allow_null=True)
    minute = serializers.IntegerField(default=46, min_value=0, max_value=130)
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class ManualScoresheetSerializer(serializers.Serializer):
    home_score = serializers.IntegerField(min_value=0)
    away_score = serializers.IntegerField(min_value=0)
    status = serializers.ChoiceField(
        choices=Match.MatchStatus.choices,
        default=Match.MatchStatus.FINISHED,
    )
    home_penalty_score = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    away_penalty_score = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    goals = ManualScoresheetGoalSerializer(many=True, required=False, default=list)
    cards = ManualScoresheetCardSerializer(many=True, required=False, default=list)
    substitutions = ManualScoresheetSubstitutionSerializer(many=True, required=False, default=list)
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    replace_existing_events = serializers.BooleanField(default=True)


