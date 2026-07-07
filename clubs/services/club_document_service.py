import logging

from django.db import transaction

from clubs.models import Club, ClubDocument
from core.models import Tenant
from media_assets.constants import AssetCategory, AssetVisibility, OwnerType
from media_assets.services import MediaAssetService

logger = logging.getLogger(__name__)


class ClubDocumentService:
    @staticmethod
    @transaction.atomic
    def upload_document(
        *,
        club: Club,
        tenant: Tenant,
        title: str,
        category: str,
        document,
        description: str = "",
        is_public: bool = False,
        valid_until=None,
        uploaded_by=None,
    ) -> ClubDocument:
        asset = MediaAssetService.upload_for_owner(
            file=document,
            owner_type=OwnerType.CLUB,
            owner_id=club.id,
            role=AssetCategory.DOCUMENT,
            name=title,
            tenant=tenant,
            uploaded_by=uploaded_by,
            visibility=AssetVisibility.INTERNAL,
            images_only=False,
        )

        return ClubDocument.objects.create(
            club=club,
            tenant=tenant,
            title=title,
            category=category,
            description=description,
            asset=asset,
            uploaded_by=uploaded_by,
            is_public=is_public,
            valid_until=valid_until,
        )

    @staticmethod
    @transaction.atomic
    def remove_document(*, document: ClubDocument) -> None:
        asset_id = document.asset_id
        document.delete()
        if asset_id:
            try:
                MediaAssetService.delete_asset(asset_id=str(asset_id))
            except Exception:
                logger.exception("Failed to delete club document asset %s", asset_id)
