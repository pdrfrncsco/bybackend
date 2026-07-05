import logging

from django.db import transaction

from clubs.models import Club, ClubSponsor
from core.models import Tenant
from media_assets.constants import AssetCategory, AssetVisibility, OwnerType
from media_assets.services import MediaAssetService

logger = logging.getLogger(__name__)


class ClubSponsorService:
    @staticmethod
    @transaction.atomic
    def create_sponsor(
        *,
        club: Club,
        tenant: Tenant,
        name: str,
        sponsor_type: str,
        description: str = "",
        website: str | None = None,
        logo=None,
        is_active: bool = True,
        sort_order: int = 0,
        uploaded_by=None,
    ) -> ClubSponsor:
        logo_asset = None
        if logo is not None:
            logo_asset = MediaAssetService.upload_for_owner(
                file=logo,
                owner_type=OwnerType.CLUB,
                owner_id=club.id,
                role=AssetCategory.SPONSOR_LOGO,
                name=f"{name} Logo",
                tenant=tenant,
                uploaded_by=uploaded_by,
                visibility=AssetVisibility.PUBLIC,
                images_only=True,
            )

        return ClubSponsor.objects.create(
            club=club,
            tenant=tenant,
            name=name,
            sponsor_type=sponsor_type,
            description=description,
            website=website or "",
            logo_asset=logo_asset,
            uploaded_by=uploaded_by,
            is_active=is_active,
            sort_order=sort_order,
        )

    @staticmethod
    @transaction.atomic
    def delete_sponsor(*, sponsor: ClubSponsor) -> None:
        logo_asset_id = sponsor.logo_asset_id
        sponsor.delete()
        if logo_asset_id:
            try:
                MediaAssetService.delete_asset(asset_id=str(logo_asset_id))
            except Exception:
                logger.exception("Failed to delete club sponsor asset %s", logo_asset_id)
