import logging

from django.db import transaction

from media_assets.constants import AssetCategory, AssetVisibility, OwnerType
from media_assets.exceptions import InvalidMediaFile, MediaAssetTooLarge, UnsupportedMediaType
from media_assets.services import MediaAssetService
from players.models import PlayerDocument

logger = logging.getLogger(__name__)


class PlayerDocumentService:
    @staticmethod
    @transaction.atomic
    def upload_document(
        *,
        player,
        title: str,
        category: str,
        document,
        description: str = "",
        valid_from=None,
        valid_until=None,
        club=None,
        is_private: bool = False,
        uploaded_by=None,
    ) -> PlayerDocument:
        visibility = AssetVisibility.PRIVATE if is_private else AssetVisibility.INTERNAL

        try:
            asset = MediaAssetService.upload_for_owner(
                file=document,
                owner_type=OwnerType.PLAYER,
                owner_id=player.id,
                role=AssetCategory.DOCUMENT,
                name=title,
                tenant=None,
                uploaded_by=uploaded_by,
                visibility=visibility,
                images_only=False,
            )
        except (InvalidMediaFile, MediaAssetTooLarge, UnsupportedMediaType) as exc:
            raise ValueError(str(exc.detail if hasattr(exc, "detail") else exc)) from exc

        return PlayerDocument.objects.create(
            player=player,
            title=title,
            category=category,
            description=description,
            asset=asset,
            valid_from=valid_from,
            valid_until=valid_until,
            club=club,
            is_private=is_private,
            uploaded_by=uploaded_by,
        )

    @staticmethod
    @transaction.atomic
    def create_from_asset(
        *,
        player,
        title: str,
        category: str,
        asset,
        description: str = "",
        valid_from=None,
        valid_until=None,
        club=None,
        is_private: bool = False,
        uploaded_by=None,
    ) -> PlayerDocument:
        return PlayerDocument.objects.create(
            player=player,
            title=title,
            category=category,
            description=description,
            asset=asset,
            valid_from=valid_from,
            valid_until=valid_until,
            club=club,
            is_private=is_private,
            uploaded_by=uploaded_by,
        )

    @staticmethod
    @transaction.atomic
    def remove_document(*, document: PlayerDocument) -> None:
        asset_id = document.asset_id
        document.delete()
        if asset_id:
            try:
                MediaAssetService.delete_asset(asset_id=str(asset_id))
            except Exception:
                logger.exception("Failed to delete player document asset %s", asset_id)
