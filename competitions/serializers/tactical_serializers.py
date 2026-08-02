from rest_framework import serializers


class TacticalPositionSerializer(serializers.Serializer):
    player_id = serializers.UUIDField()
    x = serializers.FloatField(min_value=0.0, max_value=1.0)
    y = serializers.FloatField(min_value=0.0, max_value=1.0)
    number = serializers.IntegerField(required=False, allow_null=True)
    name = serializers.CharField(required=False, allow_blank=True)


class TacticalPositionsInputSerializer(serializers.Serializer):
    club = serializers.UUIDField()
    positions = TacticalPositionSerializer(many=True)
    version = serializers.UUIDField(required=False)


class TacticalPositionsSerializer(serializers.Serializer):
    match = serializers.UUIDField()
    club = serializers.UUIDField()
    positions = TacticalPositionSerializer(many=True)
    version = serializers.UUIDField()
    updated_at = serializers.DateTimeField()
