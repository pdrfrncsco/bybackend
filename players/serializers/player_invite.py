from rest_framework import serializers
from players.models import PlayerInvite


class PlayerInviteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerInvite
        fields = [
            'id',
            'token',
            'email',
            'first_name',
            'last_name',
            'invited_by',
            'club',
            'expires_at',
            'redeemed',
            'redeemed_at',
            'created_at',
        ]
        read_only_fields = ['id', 'token', 'invited_by', 'redeemed', 'redeemed_at', 'created_at']
