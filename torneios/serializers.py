from rest_framework import serializers
from .models import Tournament, TournamentGroup
from clubes.serializers import ClubListSerializer
from clubes.models import Club
from partidas.serializers import MatchSerializer
import re

class TournamentGroupSerializer(serializers.ModelSerializer):
    clubs = ClubListSerializer(many=True, read_only=True)
    club_ids = serializers.PrimaryKeyRelatedField(many=True, queryset=Club.objects.all(), write_only=True, required=False)
    tournament = serializers.PrimaryKeyRelatedField(queryset=Tournament.objects.all())
    
    class Meta:
        model = TournamentGroup
        fields = ['id', 'name', 'tournament', 'clubs', 'club_ids']

    def create(self, validated_data):
        club_ids = validated_data.pop('club_ids', [])
        group = super().create(validated_data)
        if club_ids:
            group.clubs.set(club_ids)
        return group

    def update(self, instance, validated_data):
        club_ids = validated_data.pop('club_ids', None)
        group = super().update(instance, validated_data)
        if club_ids is not None:
            group.clubs.set(club_ids)
        return group

class TournamentSerializer(serializers.ModelSerializer):
    clubs_count = serializers.IntegerField(source='clubs.count', read_only=True)
    logo_url = serializers.ImageField(source='logo', read_only=True)
    clubs = serializers.PrimaryKeyRelatedField(many=True, queryset=Club.objects.all(), required=False, write_only=True)
    champion_club = serializers.PrimaryKeyRelatedField(queryset=Club.objects.all(), allow_null=True, required=False)
    runner_up_club = serializers.PrimaryKeyRelatedField(queryset=Club.objects.all(), allow_null=True, required=False)
    last_activity = serializers.DateTimeField(read_only=True)
    
    class Meta:
        model = Tournament
        fields = [
            'id', 'name', 'season', 'start_date', 'end_date', 'status', 
            'logo', 'logo_url', 'max_teams', 'type', 'clubs_count', 'progress', 'is_public',
            'created_at', 'clubs', 'champion_club', 'runner_up_club', 'last_activity'
        ]
        read_only_fields = ['id', 'created_at', 'tenant', 'progress']

class TournamentDetailSerializer(TournamentSerializer):
    clubs = ClubListSerializer(many=True, read_only=True)
    matches = serializers.SerializerMethodField()
    groups = TournamentGroupSerializer(many=True, read_only=True)

    class Meta(TournamentSerializer.Meta):
        fields = TournamentSerializer.Meta.fields + ['clubs', 'matches', 'groups']

    def get_matches(self, obj):
        queryset = obj.matches.all()

        def parse_round_number(value):
            if not value:
                return 10**9
            match = re.search(r"\d+", value)
            if not match:
                return 10**9
            return int(match.group())

        ordered = sorted(
            queryset,
            key=lambda m: (parse_round_number(m.round), m.date),
        )
        return MatchSerializer(ordered, many=True, context=self.context).data
