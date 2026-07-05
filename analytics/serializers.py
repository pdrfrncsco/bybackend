from rest_framework import serializers


class DashboardFilterSerializer(serializers.Serializer):
    competition_id = serializers.UUIDField(required=False)
    club_id = serializers.UUIDField(required=False)
    period = serializers.ChoiceField(
        choices=["all", "7d", "30d", "90d", "365d", "season"],
        required=False,
        default="all",
    )
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)

    def validate(self, attrs):
        start_date = attrs.get("start_date")
        end_date = attrs.get("end_date")
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError("start_date cannot be after end_date.")
        return attrs


class DashboardKpisSerializer(serializers.Serializer):
    total_clubs = serializers.IntegerField()
    total_players = serializers.IntegerField()
    total_news = serializers.IntegerField()
    active_tournaments = serializers.IntegerField()
    tournaments_upcoming = serializers.IntegerField()
    tournaments_completed = serializers.IntegerField()
    matches_finished = serializers.IntegerField()
    matches_scheduled = serializers.IntegerField()
    matches_live = serializers.IntegerField()
    total_matches = serializers.IntegerField()
    matches_today = serializers.IntegerField()
    players_this_month = serializers.IntegerField()
    players_last_month = serializers.IntegerField()
    goals_total = serializers.IntegerField()
    avg_goals_per_match = serializers.FloatField()
    organization_subscribers = serializers.IntegerField()
    total_revenue = serializers.IntegerField()
    avg_subscribers_per_tournament = serializers.FloatField()


class DashboardTournamentSummarySerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    status = serializers.CharField()
    progress = serializers.IntegerField()
    teams = serializers.IntegerField()
    logo = serializers.URLField(allow_null=True)


class DashboardTopClubSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    players = serializers.IntegerField()
    acronym = serializers.CharField()
    logo = serializers.URLField(allow_null=True)
    goals = serializers.IntegerField()


class DashboardTopScorerSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    nickname = serializers.CharField()
    club = serializers.CharField(allow_blank=True)
    club_logo = serializers.URLField(allow_null=True)
    avatar = serializers.URLField(allow_null=True)
    goals = serializers.IntegerField()


class DashboardMatchSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    tournament = serializers.CharField()
    status = serializers.ChoiceField(choices=["scheduled", "live", "finished"])
    date = serializers.DateTimeField()
    home_name = serializers.CharField()
    home_logo = serializers.URLField(allow_null=True)
    home_score = serializers.IntegerField(allow_null=True)
    away_name = serializers.CharField()
    away_logo = serializers.URLField(allow_null=True)
    away_score = serializers.IntegerField(allow_null=True)


class GoalsEvolutionPeriodSerializer(serializers.Serializer):
    period = serializers.CharField()
    goals = serializers.IntegerField()


class GoalsEvolutionSerializer(serializers.Serializer):
    tournament_name = serializers.CharField()
    periods = GoalsEvolutionPeriodSerializer(source="data", many=True)

    def to_representation(self, instance):
        payload = super().to_representation(instance)
        payload["data"] = payload.pop("periods", [])
        return payload


class DashboardOverviewSerializer(serializers.Serializer):
    kpis = DashboardKpisSerializer()
    tournaments = DashboardTournamentSummarySerializer(many=True)
    top_clubs_by_players = DashboardTopClubSerializer(many=True)
    top_scorers = DashboardTopScorerSerializer(many=True)
    goals_evolution = GoalsEvolutionSerializer(many=True)
    live_matches = DashboardMatchSerializer(many=True)
    upcoming_matches = DashboardMatchSerializer(many=True)


class PublicStatsSerializer(serializers.Serializer):
    total_clubs = serializers.IntegerField()
    total_players = serializers.IntegerField()
    active_tournaments = serializers.IntegerField()
    total_matches = serializers.IntegerField()
