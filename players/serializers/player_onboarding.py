from rest_framework import serializers
from players.models import PlayerOnboardingStatus


class PlayerOnboardingStatusSerializer(serializers.ModelSerializer):
    progress = serializers.SerializerMethodField()

    class Meta:
        model = PlayerOnboardingStatus
        fields = [
            'player',
            'current_step',
            'account_complete',
            'identity_complete',
            'personal_complete',
            'football_complete',
            'contact_complete',
            'guardian_complete',
            'club_complete',
            'review_complete',
            'completed_at',
            'progress',
        ]
        read_only_fields = fields

    def get_progress(self, obj):
        return obj.progress_percentage
