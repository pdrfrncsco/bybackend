"""
BOLAYETU — Storage Provider Factory

Returns the correct storage backend based on Django settings.

Usage:
    from media_assets.storage import get_storage_provider

    provider = get_storage_provider()
    url = provider.upload(file_obj=f, object_key="logos/uuid.jpg", content_type="image/jpeg")

The factory checks USE_CLOUDFLARE_R2 from settings.
    - True  → R2StorageProvider (production)
    - False → LocalStorageProvider (development)
"""

from django.conf import settings

from media_assets.storage.base import StorageProvider
from media_assets.storage.local import LocalStorageProvider


def get_storage_provider() -> StorageProvider:
    """
    Factory function — returns the appropriate StorageProvider.

    In production (USE_CLOUDFLARE_R2=True): returns R2StorageProvider.
    In development:                          returns LocalStorageProvider.
    """
    use_r2 = getattr(settings, "USE_CLOUDFLARE_R2", False)

    if use_r2:
        from media_assets.storage.r2 import R2StorageProvider
        return R2StorageProvider()

    return LocalStorageProvider()
