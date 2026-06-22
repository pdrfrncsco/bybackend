from rest_framework import serializers
from .models import Standing


class StandingSerializer(serializers.ModelSerializer):
    club_name = serializers.CharField(source='club.name', read_only=True)
    club_logo_url = serializers.SerializerMethodField()

    class Meta:
        model = Standing
        fields = [
            'id',
            'tournament',
            'group',
            'club',
            'club_name',
            'club_logo_url',
            'played',
            'wins',
            'draws',
            'losses',
            'goals_for',
            'goals_against',
            'points',
        ]
        read_only_fields = ['id', 'tenant']

    def get_club_logo_url(self, obj) -> str | None:
        request = self.context.get('request')
        club = getattr(obj, 'club', None)
        if not club:
            return None
        logo = getattr(club, 'logo', None)
        if not logo or not getattr(logo, 'name', None):
            return None
        try:
            storage = logo.storage
            if not storage.exists(logo.name):
                return None
            url = logo.url
        except Exception:
            return None
        return request.build_absolute_uri(url) if request else url
