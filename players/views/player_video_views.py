"""
BOLAYETU — Player Video Views

API endpoints for player videos.

Endpoints:
    GET    /api/v1/players/{slug}/videos/           — List player videos
    POST   /api/v1/players/{slug}/videos/           — Upload a video
    GET    /api/v1/players/{slug}/videos/{id}/      — Get video detail
    PATCH  /api/v1/players/{slug}/videos/{id}/      — Update video
    DELETE /api/v1/players/{slug}/videos/{id}/      — Delete video
    POST   /api/v1/players/{slug}/videos/{id}/publish/ — Publish video
"""

from drf_spectacular.utils import extend_schema
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.views import APIView

from common.responses import error_response, success_response
from common.pagination import StandardPagination
from competitions.models import Match
from players.models import PlayerVideo
from players.selectors import PlayerSelector
from players.serializers.player_video import (
    PlayerVideoSerializer,
    PlayerVideoCreateSerializer,
    PlayerVideoUpdateSerializer,
    PlayerVideoPublishSerializer,
)
from players.services.player_video_service import PlayerVideoService
from players.views.player_media_helpers import (
    player_can_view_all_content,
    player_read_permissions,
    player_write_permission,
    player_write_permissions,
)


class PlayerVideoListView(APIView):
    """
    GET:  List videos for a player.
    POST: Upload a new video via DAM or external URL.
    """

    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return player_read_permissions()
        return player_write_permissions()

    @extend_schema(
        tags=["players"],
        summary="List player videos",
        responses={200: PlayerVideoSerializer(many=True)},
    )
    def get(self, request, slug: str):
        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        if player_can_view_all_content(request, player):
            videos = player.videos.all()
        else:
            videos = player.videos.filter(status=PlayerVideo.VideoStatus.PUBLISHED)

        videos = videos.select_related("media_asset", "match")

        paginator = StandardPagination()
        page = paginator.paginate_queryset(videos, request)
        serializer = PlayerVideoSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        tags=["players"],
        summary="Upload a player video",
        request=PlayerVideoCreateSerializer,
        responses={201: PlayerVideoSerializer},
    )
    def post(self, request, slug: str):
        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        permission_error = player_write_permission(request, player)
        if permission_error:
            return permission_error

        serializer = PlayerVideoCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Validation error.",
                errors=serializer.errors,
                status_code=400,
            )

        validated = serializer.validated_data
        match = None
        match_id = validated.get("match")
        if match_id:
            match = Match.objects.filter(id=match_id).first()
            if not match:
                return error_response(message="Match not found.", status_code=400)

        try:
            if validated.get("video"):
                video = PlayerVideoService.upload_video(
                    player=player,
                    title=validated["title"],
                    video_type=validated["video_type"],
                    video_file=validated["video"],
                    description=validated.get("description", ""),
                    thumbnail_url=validated.get("thumbnail_url", ""),
                    match=match,
                    is_featured=validated.get("is_featured", False),
                    order=validated.get("order"),
                    uploaded_by=request.user,
                )
            else:
                video = PlayerVideoService.create_from_fields(
                    player=player,
                    title=validated["title"],
                    video_type=validated["video_type"],
                    video_url=validated.get("video_url"),
                    media_asset=validated.get("media_asset_instance"),
                    description=validated.get("description", ""),
                    thumbnail_url=validated.get("thumbnail_url", ""),
                    match=match,
                    is_featured=validated.get("is_featured", False),
                    order=validated.get("order"),
                )
        except ValueError as exc:
            return error_response(message=str(exc), status_code=400)

        result = PlayerVideoSerializer(video)
        return success_response(
            data=result.data,
            message="Video uploaded successfully. It will be published after processing.",
            status_code=201,
        )


class PlayerVideoDetailView(APIView):
    """
    GET:   Get video details.
    PATCH: Update video.
    DELETE: Delete video.
    """

    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return player_read_permissions()
        return player_write_permissions()

    @extend_schema(
        tags=["players"],
        summary="Get player video detail",
        responses={200: PlayerVideoSerializer},
    )
    def get(self, request, slug: str, video_id: str):
        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        try:
            video = player.videos.select_related("media_asset", "match").get(id=video_id)
        except PlayerVideo.DoesNotExist:
            return error_response(message="Video not found.", status_code=404)

        if video.status != PlayerVideo.VideoStatus.PUBLISHED and not player_can_view_all_content(request, player):
            return error_response(message="Video not found.", status_code=404)

        serializer = PlayerVideoSerializer(video)
        return success_response(data=serializer.data)

    @extend_schema(
        tags=["players"],
        summary="Update player video",
        request=PlayerVideoUpdateSerializer,
        responses={200: PlayerVideoSerializer},
    )
    def patch(self, request, slug: str, video_id: str):
        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        permission_error = player_write_permission(request, player)
        if permission_error:
            return permission_error

        try:
            video = player.videos.get(id=video_id)
        except PlayerVideo.DoesNotExist:
            return error_response(message="Video not found.", status_code=404)

        serializer = PlayerVideoUpdateSerializer(
            video, data=request.data, partial=True
        )
        if not serializer.is_valid():
            return error_response(
                message="Validation error.",
                errors=serializer.errors,
                status_code=400,
            )

        serializer.save()
        result = PlayerVideoSerializer(video)
        return success_response(data=result.data, message="Video updated successfully.")

    @extend_schema(
        tags=["players"],
        summary="Delete player video",
        responses={204: None},
    )
    def delete(self, request, slug: str, video_id: str):
        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        permission_error = player_write_permission(request, player)
        if permission_error:
            return permission_error

        try:
            video = player.videos.get(id=video_id)
        except PlayerVideo.DoesNotExist:
            return error_response(message="Video not found.", status_code=404)

        PlayerVideoService.remove_video(video=video)
        return success_response(message="Video deleted successfully.")


class PlayerVideoPublishView(APIView):
    """
    POST: Publish a video.
    """

    def get_permissions(self):
        return player_write_permissions()

    @extend_schema(
        tags=["players"],
        summary="Publish player video",
        request=PlayerVideoPublishSerializer,
        responses={200: PlayerVideoSerializer},
    )
    def post(self, request, slug: str, video_id: str):
        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        permission_error = player_write_permission(request, player)
        if permission_error:
            return permission_error

        try:
            video = player.videos.get(id=video_id)
        except PlayerVideo.DoesNotExist:
            return error_response(message="Video not found.", status_code=404)

        video.status = PlayerVideo.VideoStatus.PUBLISHED
        video.save(update_fields=["status"])

        serializer = PlayerVideoSerializer(video)
        return success_response(data=serializer.data, message="Video published successfully.")
