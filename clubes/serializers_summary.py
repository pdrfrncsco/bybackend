from rest_framework import serializers
from .models import Club


class ClubSummarySerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = Club
        fields = ["id", "display_name", "short_name", "acronym", "name", "logo"]
        read_only_fields = ["id"]

    def get_display_name(self, obj):
        if obj.short_name:
            return obj.short_name
        if obj.acronym:
            return obj.acronym
        return obj.name

