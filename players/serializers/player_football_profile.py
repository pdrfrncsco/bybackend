from rest_framework import serializers

from players.models import PlayerFootballProfile


class PlayerFootballProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerFootballProfile
        fields = [
            "player",
            "primary_position",
            "shirt_number",
            "height_cm",
            "weight_kg",
            "foot",
            "total_matches",
            "total_goals",
            "total_assists",
        ]
        read_only_fields = ["player",]
