"""
BOLAYETU — Player Video Views

API endpoints for player videos.

Endpoints:
    GET    /api/v1/players/{slug}/videos/           — List player videos
    POST   /api/v1/players/{slug}/videos/           — Upload a video (staff only)
    GET    /api/v1/players/{slug}/videos/{id}/      — Get video detail
    PATCH  /api/v1/players/{slug}/videos/{id}/      — Update video (staff only)
    DELETE /api/v1/players/{slug}/videos/{id}/      — Delete video (staff only)
    POST   /api/v1/players/{slug}/videos/{id}/publish/ — Publish video (staff only)
"""

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from common.responses import success_response, error_response
from common.pagination import StandardPagination
from players.models import Player, PlayerVideo
from players.selectors import PlayerSelector
from players.serializers.player_video import (
    PlayerVideoSerializer,
    PlayerVideoCreateSerializer,
    PlayerVideoUpdateSerializer,
    PlayerVideoPublishSerializer,
)
from players.permissions import IsStaffOrReadOnly


class PlayerVideoListView(APIView):
    """
    GET:  List videos for a player.
    POST: Upload a new video (staff only).
    """

    permission_classes = [IsStaffOrReadOnly]

    @extend_schema(
        tags=["players"],
        summary="List player videos",
        responses={200: PlayerVideoSerializer(many=True)},
    )
    def get(self, request, slug: str):
        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        # Public users only see published videos
        if request.user.is_authenticated and request.user.is_staff:
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
        summary="Upload a player video (staff only)",
        request=PlayerVideoCreateSerializer,
        responses={201: PlayerVideoSerializer},
    )
    def post(self, request, slug: str):
        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        serializer = PlayerVideoCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Validation error.",
                errors=serializer.errors,
                status_code=400,
            )

        video = PlayerVideo.objects.create(
            player=player,
            status=PlayerVideo.VideoStatus.DRAFT,
            **serializer.validated_data,
        )

        result = PlayerVideoSerializer(video)
        return success_response(
            data=result.data,
            message="Video uploaded successfully. It will be published after processing.",
            status_code=201,
        )


class PlayerVideoDetailView(APIView):
    """
    GET:   Get video details.
    PATCH: Update video (staff only).
    DELETE: Delete video (staff only).
    """

    permission_classes = [IsStaffOrReadOnly]

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

        # Check visibility permissions
        if video.status != PlayerVideo.VideoStatus.PUBLISHED and not (
            request.user.is_authenticated and request.user.is_staff
        ):
            return error_response(message="Video not found.", status_code=404)

        serializer = PlayerVideoSerializer(video)
        return success_response(data=serializer.data)

    @extend_schema(
        tags=["players"],
        summary="Update player video (staff only)",
        request=PlayerVideoUpdateSerializer,
        responses={200: PlayerVideoSerializer},
    )
    def patch(self, request, slug: str, video_id: str):
        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

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
        summary="Delete player video (staff only)",
        responses={204: None},
    )
    def delete(self, request, slug: str, video_id: str):
        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        try:
            video = player.videos.get(id=video_id)
        except PlayerVideo.DoesNotExist:
            return error_response(message="Video not found.", status_code=404)

        video.delete()
        return success_response(message="Video deleted successfully.")


class PlayerVideoPublishView(APIView):
    """
    POST: Publish a video (staff only).
    """

    permission_classes = [IsStaffOrReadOnly]

    @extend_schema(
        tags=["players"],
        summary="Publish player video (staff only)",
        request=PlayerVideoPublishSerializer,
        responses={200: PlayerVideoSerializer},
    )
    def post(self, request, slug: str, video_id: str):
        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        try:
            video = player.videos.get(id=video_id)
        except PlayerVideo.DoesNotExist:
            return error_response(message="Video not found.", status_code=404)

        video.status = PlayerVideo.VideoStatus.PUBLISHED
        video.save(update_fields=["status"])

        serializer = PlayerVideoSerializer(video)
        return success_response(data=serializer.data, message="Video published successfully.")
