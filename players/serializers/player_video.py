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


class PlayerVideoCreateSerializer(serializers.Serializer):
    """
    Serializer for uploading a new player video.

    Accepts an external URL, a file upload (`video`), or a pre-existing DAM asset UUID.
    """

    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    video_type = serializers.ChoiceField(choices=PlayerVideo.VideoType.choices)
    video_url = serializers.URLField(required=False, allow_blank=True, default="")
    thumbnail_url = serializers.URLField(required=False, allow_blank=True, default="")
    video = serializers.FileField(required=False)
    media_asset = serializers.UUIDField(required=False)
    match = serializers.UUIDField(required=False, allow_null=True)
    is_featured = serializers.BooleanField(required=False, default=False)
    order = serializers.IntegerField(required=False, allow_null=True, min_value=0)

    def validate(self, data):
        video_url = (data.get("video_url") or "").strip()
        video_file = data.get("video")
        media_asset_id = data.get("media_asset")

        if not video_url and not video_file and not media_asset_id:
            raise serializers.ValidationError(
                "Either video_url, video file, or media_asset UUID must be provided."
            )

        provided_sources = sum(bool(value) for value in (video_url, video_file, media_asset_id))
        if provided_sources > 1:
            raise serializers.ValidationError(
                "Provide only one source: video_url, video file, or media_asset UUID."
            )

        if media_asset_id:
            from media_assets.constants import AssetType
            from media_assets.models import MediaAsset

            try:
                asset = MediaAsset.objects.get(id=media_asset_id)
            except MediaAsset.DoesNotExist as exc:
                raise serializers.ValidationError({"media_asset": "Asset not found."}) from exc

            if asset.asset_type != AssetType.VIDEO:
                raise serializers.ValidationError({"media_asset": "Asset must be a video type."})

            data["media_asset_instance"] = asset

        data["video_url"] = video_url or None
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
