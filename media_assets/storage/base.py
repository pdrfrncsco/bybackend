"""
BOLAYETU — Storage Provider Abstraction

Defines the interface that all storage backends must implement.
This allows swapping the storage provider (local dev, Cloudflare R2)
without changing the business logic.

Architecture (08_MEDIA_STORAGE_ARCHITECTURE.md §27):
    StorageProvider interface:
        upload()
        download()
        delete()
        generate_signed_url()
        exists()
        copy()
        move()
"""

import abc
import io
from typing import BinaryIO


class StorageProvider(abc.ABC):
    """
    Abstract interface for all storage backends.

    Concrete implementations:
        - LocalStorageProvider   — dev/test (local filesystem)
        - R2StorageProvider      — production (Cloudflare R2 via boto3)
    """

    @abc.abstractmethod
    def upload(
        self,
        *,
        file_obj: BinaryIO,
        object_key: str,
        content_type: str,
        public: bool = True,
    ) -> str:
        """
        Upload a file to storage.

        Args:
            file_obj:     File-like object (seeked to start).
            object_key:   Path/key within the bucket.
            content_type: MIME type of the file.
            public:       Whether the object should be publicly accessible.

        Returns:
            The public URL (CDN URL in production, local URL in dev).
        """

    @abc.abstractmethod
    def delete(self, *, object_key: str) -> None:
        """Delete an object from storage."""

    @abc.abstractmethod
    def exists(self, *, object_key: str) -> bool:
        """Check whether an object exists in storage."""

    @abc.abstractmethod
    def generate_signed_url(self, *, object_key: str, expires_in: int = 3600) -> str:
        """
        Generate a temporary signed URL for a private object.

        Args:
            object_key: Path/key within the bucket.
            expires_in: Expiration time in seconds (default: 1 hour).

        Returns:
            A signed URL string.
        """

    def get_public_url(self, *, object_key: str) -> str:
        """
        Return the public URL for an object (no signing required).
        Must be overridden if the default behaviour is insufficient.
        """
        raise NotImplementedError
