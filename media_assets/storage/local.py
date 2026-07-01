"""
BOLAYETU — Local Filesystem Storage Provider

Used in development and testing environments.

Files are stored in MEDIA_ROOT and served via Django's MEDIA_URL.
This is never used in production — see R2StorageProvider.
"""

import os
from typing import BinaryIO

from django.conf import settings
from django.core.files.storage import default_storage

from media_assets.storage.base import StorageProvider


class LocalStorageProvider(StorageProvider):
    """
    Local development storage backend.

    Stores files using Django's default_storage (MEDIA_ROOT).
    Public URLs are built from MEDIA_URL.
    """

    def upload(
        self,
        *,
        file_obj: BinaryIO,
        object_key: str,
        content_type: str,
        public: bool = True,
    ) -> str:
        """
        Save file to MEDIA_ROOT using Django's default_storage.
        Returns the relative URL (MEDIA_URL + object_key).
        """
        from django.core.files.base import ContentFile

        # Read content
        content = file_obj.read()

        # Save via default_storage (handles MEDIA_ROOT)
        # If the file already exists, default_storage will generate a unique name
        saved_name = default_storage.save(object_key, ContentFile(content))

        # Build public URL
        media_url = settings.MEDIA_URL.rstrip("/")
        return f"{media_url}/{saved_name}"

    def delete(self, *, object_key: str) -> None:
        """Delete a file from local storage."""
        if default_storage.exists(object_key):
            default_storage.delete(object_key)

    def exists(self, *, object_key: str) -> bool:
        """Check if a file exists in local storage."""
        return default_storage.exists(object_key)

    def generate_signed_url(self, *, object_key: str, expires_in: int = 3600) -> str:
        """
        Local storage doesn't support signed URLs.
        Returns the plain public URL instead.
        """
        return self.get_public_url(object_key=object_key)

    def get_public_url(self, *, object_key: str) -> str:
        """Build a public URL for an object key."""
        media_url = settings.MEDIA_URL.rstrip("/")
        return f"{media_url}/{object_key}"
