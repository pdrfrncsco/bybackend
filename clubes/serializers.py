from rest_framework import serializers
from drf_writable_nested.serializers import WritableNestedModelSerializer
from .models import Club, ClubHistory, Staff


class ClubBasicSerializer(serializers.ModelSerializer):
    logo_url = serializers.ImageField(source='logo', read_only=True)

    class Meta:
        model = Club
        fields = ['id', 'name', 'short_name', 'acronym', 'logo_url', 'primary_color', 'secondary_color']


class ClubHistorySerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=False)
    club_name = serializers.CharField(source='club.name', read_only=True)

    class Meta:
        model = ClubHistory
        fields = ['id', 'season', 'tournament_name', 'placement', 'is_trophy', 'club_name']

class StaffSerializer(serializers.ModelSerializer):
    club_name = serializers.CharField(source='club.name', read_only=True)
    photo_url = serializers.ImageField(source='photo', read_only=True)

    class Meta:
        model = Staff
        fields = [
            'id', 'tenant', 'club', 'club_name', 'name', 'role', 
            'date_of_birth', 'nationality', 'photo', 'photo_url',
            'email', 'phone', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'tenant', 'created_at', 'updated_at']

class ClubSerializer(WritableNestedModelSerializer):
    history = ClubHistorySerializer(many=True, required=False)
    active_players = serializers.SerializerMethodField()
    logo_url = serializers.ImageField(source='logo', read_only=True)
    staff_members = StaffSerializer(many=True, read_only=True)

    class Meta:
        model = Club
        fields = [
            'id', 'name', 'short_name', 'acronym', 'founded_year', 'logo', 'logo_url', 'location', 
            'president', 'email', 'phone', 'website', 
            'stadium_name', 'stadium_capacity',
            'primary_color', 'secondary_color', 'created_at', 'updated_at',
            'history', 'active_players', 'staff_members', 'organizacao'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'tenant']

    def get_active_players(self, obj) -> int:
        return obj.players.filter(status='active').count()
    
    def update(self, instance, validated_data):
        # Handle deletion of history items that are not in the request
        history_data = validated_data.get('history')
        if history_data is not None:
            # Get IDs of history items in the request
            history_ids = [item.get('id') for item in history_data if item.get('id')]
            # Delete history items that are not in the request
            instance.history.exclude(id__in=history_ids).delete()
        
        return super().update(instance, validated_data)

class ClubListSerializer(serializers.ModelSerializer):
    active_players = serializers.SerializerMethodField()
    logo_url = serializers.ImageField(source='logo', read_only=True)

    class Meta:
        model = Club
        fields = ['id', 'name', 'short_name', 'acronym', 'logo', 'logo_url', 'location', 'primary_color', 'active_players', 'founded_year', 'stadium_name', 'organizacao']

    def get_active_players(self, obj) -> int:
        return obj.players.filter(status='active').count()
