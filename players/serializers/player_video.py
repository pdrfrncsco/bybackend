"""
BOLAYETU — Player Video Serializers

Serializers for player video endpoints.
"""

from rest_framework import serializers

from players.models import PlayerVideo


class PlayerVideoSerializer(serializers.ModelSerializer):
    """
    Serializer for viewing player videos.
    
    Used for: GET /api/v1/players/{slug}/videos/
    """
    
    video_type_label = serializers.SerializerMethodField()
    status_label = serializers.SerializerMethodField()
    url = serializers.ReadOnlyField()
    thumbnail = serializers.ReadOnlyField()
    match_info = serializers.SerializerMethodField()
    
    class Meta:
        model = PlayerVideo
        fields = [
            "id",
            "title",
            "description",
            "video_type",
            "video_type_label",
            "url",
            "thumbnail_url",
            "thumbnail",
            "video_url",
            "media_asset",
            "duration_seconds",
            "status",
            "status_label",
            "is_featured",
            "order",
            "match",
            "match_info",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "duration_seconds",
            "status",
            "created_at",
            "updated_at",
        ]
    
    def get_video_type_label(self, obj: PlayerVideo) -> str:
        return obj.get_video_type_display()
    
    def get_status_label(self, obj: PlayerVideo) -> str:
        return obj.get_status_display()
    
    def get_match_info(self, obj: PlayerVideo) -> dict | None:
        if obj.match:
            return {
                "id": obj.match.id,
                "home_club": obj.match.home_club.name,
                "away_club": obj.match.away_club.name,
                "date": obj.match.date,
                "competition": obj.match.competition.name if obj.match.competition else None,
            }
        return None


class PlayerVideoCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for uploading a new player video.
    
    Used for: POST /api/v1/players/{slug}/videos/
    """
    
    class Meta:
        model = PlayerVideo
        fields = [
            "title",
            "description",
            "video_type",
            "video_url",
            "thumbnail_url",
            "media_asset",
            "match",
            "is_featured",
            "order",
        ]
    
    def validate(self, data):
        """Validate that either video_url or media_asset is provided."""
        video_url = data.get("video_url")
        media_asset = data.get("media_asset")
        
        if not video_url and not media_asset:
            raise serializers.ValidationError(
                "Either video_url or media_asset must be provided."
            )
        
        return data


class PlayerVideoUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating a player video.
    
    Used for: PATCH /api/v1/players/{slug}/videos/{id}/
    """
    
    class Meta:
        model = PlayerVideo
        fields = [
            "title",
            "description",
            "video_type",
            "video_url",
            "thumbnail_url",
            "media_asset",
            "match",
            "is_featured",
            "order",
            "status",
        ]


class PlayerVideoPublishSerializer(serializers.Serializer):
    """
    Serializer for publishing a player video.
    
    Used for: POST /api/v1/players/{slug}/videos/{id}/publish/
    """
    
    pass  # No additional fields needed - publishing is a simple action
