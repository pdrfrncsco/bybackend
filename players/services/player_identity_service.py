import logging
from django.db import transaction

from players.models import PlayerIdentityDocument

logger = logging.getLogger(__name__)


class PlayerIdentityService:
    @staticmethod
    @transaction.atomic
    def create_document(*, player, validated_data, uploaded_by=None) -> PlayerIdentityDocument:
        """Create an identity document. validated_data may include asset_instance or file under 'document'."""
        asset_instance = validated_data.pop("asset_instance", None)
        document_file = validated_data.pop("document", None)

        if asset_instance:
            # Create record pointing to existing DAM asset
            return PlayerIdentityDocument.objects.create(player=player, document_front=asset_instance, **validated_data)

        if document_file:
            # Upload via media_assets service
            try:
                from media_assets.services import MediaAssetService
                from media_assets.constants import AssetCategory, OwnerType, AssetVisibility
            except Exception as exc:
                logger.exception("MediaAsset service not available: %s", exc)
                raise ValueError("Media asset service unavailable.") from exc

            visibility = AssetVisibility.INTERNAL
            try:
                asset = MediaAssetService.upload_for_owner(
                    file=document_file,
                    owner_type=OwnerType.PLAYER,
                    owner_id=player.id,
                    role=AssetCategory.DOCUMENT,
                    name=f"{player.first_name} {player.last_name} Identity Document",
                    tenant=None,
                    uploaded_by=uploaded_by,
                    visibility=visibility,
                    images_only=False,
                )
            except Exception as exc:
                logger.exception("Failed to upload identity document: %s", exc)
                raise ValueError(str(exc)) from exc

            return PlayerIdentityDocument.objects.create(player=player, document_front=asset, **validated_data)

    @staticmethod
    @transaction.atomic
    def update_document(*, document: PlayerIdentityDocument, data) -> PlayerIdentityDocument:
        for k, v in data.items():
            setattr(document, k, v)
        document.save()
        return document

    @staticmethod
    @transaction.atomic
    def remove_document(*, document: PlayerIdentityDocument) -> None:
        asset_id = getattr(document.document_front, "id", None)
        document.delete()
        if asset_id:
            try:
                from media_assets.services import MediaAssetService
                MediaAssetService.delete_asset(asset_id=str(asset_id))
            except Exception:
                logger.exception("Failed to delete identity document asset %s", asset_id)

    @staticmethod
    @transaction.atomic
    def verify_document(*, document: PlayerIdentityDocument, verified_by) -> PlayerIdentityDocument:
        document.verification_status = "verified"
        document.verified_by = verified_by
        from django.utils import timezone
        document.verified_at = timezone.now()
        document.save(update_fields=["verification_status", "verified_by", "verified_at"])
        return document
