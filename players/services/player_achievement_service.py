import logging

from django.db import transaction

from media_assets.constants import AssetCategory, AssetVisibility, OwnerType
from media_assets.exceptions import InvalidMediaFile, MediaAssetTooLarge, UnsupportedMediaType
from media_assets.services import MediaAssetService
from players.models import PlayerAchievement

logger = logging.getLogger(__name__)


class PlayerAchievementService:
    @staticmethod
    def _upload_trophy(*, player, title: str, trophy_image, uploaded_by):
        return MediaAssetService.upload_for_owner(
            file=trophy_image,
            owner_type=OwnerType.PLAYER,
            owner_id=player.id,
            role=AssetCategory.GALLERY,
            name=f"{title} Trophy",
            tenant=None,
            uploaded_by=uploaded_by,
            visibility=AssetVisibility.PUBLIC,
            images_only=True,
        )

    @staticmethod
    def _upload_certificate(*, player, title: str, certificate, uploaded_by):
        return MediaAssetService.upload_for_owner(
            file=certificate,
            owner_type=OwnerType.PLAYER,
            owner_id=player.id,
            role=AssetCategory.CERTIFICATE,
            name=f"{title} Certificate",
            tenant=None,
            uploaded_by=uploaded_by,
            visibility=AssetVisibility.INTERNAL,
            images_only=False,
        )

    @staticmethod
    @transaction.atomic
    def create_achievement(
        *,
        player,
        title: str,
        achievement_type: str,
        level: str,
        description: str = "",
        date_achieved=None,
        season: str = "",
        competition=None,
        club=None,
        trophy_image_file=None,
        certificate_file=None,
        trophy_image_url: str = "",
        certificate_url: str = "",
        stats_snapshot=None,
        uploaded_by=None,
    ) -> PlayerAchievement:
        trophy_asset = None
        certificate_asset = None
        resolved_trophy_url = trophy_image_url or None
        resolved_certificate_url = certificate_url or None

        try:
            if trophy_image_file:
                trophy_asset = PlayerAchievementService._upload_trophy(
                    player=player,
                    title=title,
                    trophy_image=trophy_image_file,
                    uploaded_by=uploaded_by,
                )
                resolved_trophy_url = trophy_asset.public_url

            if certificate_file:
                certificate_asset = PlayerAchievementService._upload_certificate(
                    player=player,
                    title=title,
                    certificate=certificate_file,
                    uploaded_by=uploaded_by,
                )
                resolved_certificate_url = certificate_asset.public_url
        except (InvalidMediaFile, MediaAssetTooLarge, UnsupportedMediaType, ValueError) as exc:
            detail = exc.detail if hasattr(exc, "detail") else str(exc)
            raise ValueError(str(detail)) from exc

        return PlayerAchievement.objects.create(
            player=player,
            title=title,
            achievement_type=achievement_type,
            level=level,
            description=description,
            date_achieved=date_achieved,
            season=season or None,
            competition=competition,
            club=club,
            trophy_asset=trophy_asset,
            certificate_asset=certificate_asset,
            trophy_image=resolved_trophy_url,
            certificate_url=resolved_certificate_url,
            stats_snapshot=stats_snapshot,
        )

    @staticmethod
    @transaction.atomic
    def remove_achievement(*, achievement: PlayerAchievement) -> None:
        trophy_asset_id = achievement.trophy_asset_id
        certificate_asset_id = achievement.certificate_asset_id
        achievement.delete()

        for asset_id in (trophy_asset_id, certificate_asset_id):
            if asset_id:
                try:
                    MediaAssetService.delete_asset(asset_id=str(asset_id))
                except Exception:
                    logger.exception("Failed to delete player achievement asset %s", asset_id)
