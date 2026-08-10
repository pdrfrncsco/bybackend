from rest_framework import serializers

from players.models import PlayerCareer


class PlayerCareerSerializer(serializers.ModelSerializer):
    club_name = serializers.CharField(source="club.name", read_only=True)
    competition_name = serializers.CharField(source="competition.name", read_only=True)

    class Meta:
        model = PlayerCareer
        fields = [
            "id",
            "player",
            "club",
            "club_name",
            "season",
            "competition",
            "competition_name",
            "position",
            "appearances",
            "starts",
            "minutes_played",
            "goals",
            "assists",
            "yellow_cards",
            "red_cards",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
