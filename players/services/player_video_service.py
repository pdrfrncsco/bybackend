import logging

from django.db import transaction

from media_assets.constants import AssetCategory, AssetVisibility, OwnerType
from media_assets.exceptions import InvalidMediaFile, MediaAssetTooLarge, UnsupportedMediaType
from media_assets.services import MediaAssetService
from players.models import PlayerVideo

logger = logging.getLogger(__name__)


class PlayerVideoService:
    @staticmethod
    @transaction.atomic
    def upload_video(
        *,
        player,
        title: str,
        video_type: str,
        video_file,
        description: str = "",
        thumbnail_url: str = "",
        match=None,
        is_featured: bool = False,
        order=None,
        uploaded_by=None,
    ) -> PlayerVideo:
        try:
            asset = MediaAssetService.upload_for_owner(
                file=video_file,
                owner_type=OwnerType.PLAYER,
                owner_id=player.id,
                role=AssetCategory.VIDEO,
                name=title,
                tenant=None,
                uploaded_by=uploaded_by,
                visibility=AssetVisibility.PUBLIC,
                images_only=False,
            )
        except (InvalidMediaFile, MediaAssetTooLarge, UnsupportedMediaType) as exc:
            raise ValueError(str(exc.detail if hasattr(exc, "detail") else exc)) from exc

        return PlayerVideo.objects.create(
            player=player,
            title=title,
            description=description,
            video_type=video_type,
            media_asset=asset,
            thumbnail_url=thumbnail_url or None,
            match=match,
            is_featured=is_featured,
            order=0 if order is None else order,
            status=PlayerVideo.VideoStatus.DRAFT,
        )

    @staticmethod
    @transaction.atomic
    def create_from_fields(
        *,
        player,
        title: str,
        video_type: str,
        video_url: str = "",
        media_asset=None,
        description: str = "",
        thumbnail_url: str = "",
        match=None,
        is_featured: bool = False,
        order=None,
    ) -> PlayerVideo:
        return PlayerVideo.objects.create(
            player=player,
            title=title,
            description=description,
            video_type=video_type,
            video_url=video_url or None,
            media_asset=media_asset,
            thumbnail_url=thumbnail_url or None,
            match=match,
            is_featured=is_featured,
            order=0 if order is None else order,
            status=PlayerVideo.VideoStatus.DRAFT,
        )

    @staticmethod
    @transaction.atomic
    def remove_video(*, video: PlayerVideo) -> None:
        asset_id = video.media_asset_id
        video.delete()
        if asset_id:
            try:
                MediaAssetService.delete_asset(asset_id=str(asset_id))
            except Exception:
                logger.exception("Failed to delete player video asset %s", asset_id)
