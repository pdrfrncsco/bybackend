from rest_framework import serializers
from .models import Player


class PlayerSummarySerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = Player
        fields = ["id", "display_name", "shirt_name", "name", "number", "club"]
        read_only_fields = ["id"]

    def get_display_name(self, obj):
        if obj.shirt_name:
            return obj.shirt_name
        if obj.nickname:
            return obj.nickname
        return obj.name

