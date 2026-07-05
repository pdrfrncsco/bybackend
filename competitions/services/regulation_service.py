import logging
from django.db import transaction
from django.utils import timezone

from core.models import Tenant
from competitions.exceptions import DuplicateCompetitionRegulation
from competitions.models import Competition, CompetitionRegulation
from media_assets.constants import AssetCategory, OwnerType
from media_assets.models import MediaUsage
from media_assets.services import MediaAssetService

logger = logging.getLogger(__name__)


class CompetitionRegulationService:
    @staticmethod
    @transaction.atomic
    def create_regulation(
        *,
        tenant: Tenant,
        competition: Competition,
        title: str,
        document,
        summary: str = "",
        version: str = "1.0",
        status: str = CompetitionRegulation.Status.PUBLISHED,
        uploaded_by=None,
    ) -> CompetitionRegulation:
        if competition.tenant_id != tenant.id:
            raise PermissionError("Competition must belong to the same tenant.")

        if CompetitionRegulation.objects.filter(
            competition=competition,
            title=title,
            version=version,
        ).exists():
            raise DuplicateCompetitionRegulation()

        regulation = CompetitionRegulation.objects.create(
            tenant=tenant,
            competition=competition,
            title=title,
            summary=summary,
            version=version,
            status=status,
            uploaded_by=uploaded_by,
            published_at=timezone.now() if status == CompetitionRegulation.Status.PUBLISHED else None,
        )

        MediaAssetService.upload_for_owner(
            file=document,
            owner_type=OwnerType.COMPETITION_REGULATION,
            owner_id=regulation.id,
            role=AssetCategory.DOCUMENT,
            name=title,
            tenant=tenant,
            uploaded_by=uploaded_by,
            images_only=False,
        )

        logger.info("Competition regulation created: %s (%s)", regulation.title, regulation.id)
        return regulation

    @staticmethod
    def get_document_url(*, regulation: CompetitionRegulation) -> str:
        usage = MediaUsage.get_active_for(
            owner_type=OwnerType.COMPETITION_REGULATION,
            owner_id=regulation.id,
            role=AssetCategory.DOCUMENT,
        )
        return usage.asset.public_url if usage else ""

    @staticmethod
    @transaction.atomic
    def update_regulation(
        *,
        regulation: CompetitionRegulation,
        title: str | None = None,
        summary: str | None = None,
        version: str | None = None,
        status: str | None = None,
        document=None,
        uploaded_by=None,
    ) -> CompetitionRegulation:
        if title is not None:
            regulation.title = title
        if summary is not None:
            regulation.summary = summary
        if version is not None:
            regulation.version = version
        if status is not None:
            regulation.status = status
            if status == CompetitionRegulation.Status.PUBLISHED and regulation.published_at is None:
                regulation.published_at = timezone.now()

        regulation.save()

        if document is not None:
            MediaAssetService.upload_for_owner(
                file=document,
                owner_type=OwnerType.COMPETITION_REGULATION,
                owner_id=regulation.id,
                role=AssetCategory.DOCUMENT,
                name=regulation.title,
                tenant=regulation.tenant,
                uploaded_by=uploaded_by,
                images_only=False,
            )

        return regulation

    @staticmethod
    @transaction.atomic
    def archive_regulation(*, regulation: CompetitionRegulation) -> CompetitionRegulation:
        regulation.status = CompetitionRegulation.Status.ARCHIVED
        regulation.save(update_fields=["status", "updated_at"])
        MediaUsage.objects.filter(
            owner_type=OwnerType.COMPETITION_REGULATION,
            owner_id=regulation.id,
            role=AssetCategory.DOCUMENT,
        ).update(is_active=False)
        return regulation
