from rest_framework import serializers

from players.models import PlayerSeasonStatistics


class PlayerSeasonStatisticsSerializer(serializers.ModelSerializer):
    club_name = serializers.CharField(source="club.name", read_only=True)
    competition_name = serializers.CharField(source="competition.name", read_only=True)

    class Meta:
        model = PlayerSeasonStatistics
        fields = [
            "id",
            "player",
            "season",
            "club",
            "club_name",
            "competition",
            "competition_name",
            "appearances",
            "starts",
            "minutes",
            "goals",
            "assists",
            "shots",
            "shots_on_target",
            "yellow_cards",
            "red_cards",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
