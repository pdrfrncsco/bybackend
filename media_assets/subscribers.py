import logging
from typing import Any

from core.events import subscribe, Event

logger = logging.getLogger(__name__)


@subscribe("AssetUploaded")
def handle_asset_uploaded(event: Event) -> None:
    """Subscriber reacting to AssetUploaded events.

    Enqueue thumbnail generation task if available. This is a best-effort
    subscriber: failures should not block the publisher.
    """
    try:
        asset_id = event.payload.get("asset_id")
        if not asset_id:
            logger.debug("AssetUploaded event missing asset_id: %s", event)
            return

        # Try to enqueue Celery task
        try:
            from media_assets.tasks import generate_thumbnails
            generate_thumbnails.delay(asset_id)
            logger.info("Enqueued generate_thumbnails for asset %s via subscriber", asset_id)
        except Exception:
            # Fallback: call synchronous generation if available
            try:
                from media_assets.tasks import generate_thumbnails_sync
                generate_thumbnails_sync(asset_id)
                logger.info("Ran generate_thumbnails_sync for asset %s via subscriber", asset_id)
            except Exception:
                logger.debug("Thumbnail generation not available for asset %s", asset_id)
    except Exception as exc:
        logger.exception("Error handling AssetUploaded event: %s", exc)
