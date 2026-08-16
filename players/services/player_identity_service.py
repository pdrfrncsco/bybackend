import logging
from django.db import transaction

from players.models import PlayerIdentityDocument

logger = logging.getLogger(__name__)


class PlayerIdentityService:
    @staticmethod
    @transaction.atomic
    def create_document(*, player, validated_data, uploaded_by=None) -> PlayerIdentityDocument:
        """Create an identity document and persist both front and back assets when provided."""
        asset_instance = validated_data.pop("asset_instance", None)
        document_file = validated_data.pop("document", None)
        document_front_file = validated_data.pop("document_front", None)
        document_back_file = validated_data.pop("document_back", None)
        validated_data.pop("asset", None)
        validated_data["document_number"] = (validated_data.get("document_number") or "").strip()

        def upload_identity_asset(file_obj, *, side: str):
            try:
                from media_assets.services import MediaAssetService
                from media_assets.constants import AssetCategory, OwnerType, AssetVisibility
            except Exception as exc:
                logger.exception("MediaAsset service not available: %s", exc)
                raise ValueError("Media asset service unavailable.") from exc

            visibility = AssetVisibility.INTERNAL
            try:
                return MediaAssetService.upload_for_owner(
                    file=file_obj,
                    owner_type=OwnerType.PLAYER,
                    owner_id=player.id,
                    role=AssetCategory.DOCUMENT,
                    name=f"{player.first_name} {player.last_name} Identity Document {side}",
                    tenant=None,
                    uploaded_by=uploaded_by,
                    visibility=visibility,
                    images_only=False,
                )
            except Exception as exc:
                logger.exception("Failed to upload identity document %s: %s", side.lower(), exc)
                raise ValueError(str(exc)) from exc

        if asset_instance:
            front_asset = asset_instance
        elif document_front_file or document_file:
            front_asset = upload_identity_asset(document_front_file or document_file, side="Front")
        else:
            raise ValueError("The front of the identity document is required.")

        back_asset = None
        if document_back_file:
            back_asset = upload_identity_asset(document_back_file, side="Back")

        return PlayerIdentityDocument.objects.create(
            player=player,
            document_front=front_asset,
            document_back=back_asset,
            **validated_data,
        )

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
        asset_ids = [
            getattr(document.document_front, "id", None),
            getattr(document.document_back, "id", None),
        ]
        document.delete()
        for asset_id in [asset_id for asset_id in asset_ids if asset_id]:
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
