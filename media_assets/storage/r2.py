"""
BOLAYETU — Cloudflare R2 Storage Provider

Production storage backend using Cloudflare R2 (S3-compatible API).

Requirements:
    - django-storages[boto3] in requirements.txt  ✓ (already present)
    - CLOUDFLARE_R2_* env vars in .env

Architecture (08_MEDIA_STORAGE_ARCHITECTURE.md §27):
    All files in production go to R2.
    Public content is served through Cloudflare CDN (no direct R2 access).
    Private content uses pre-signed URLs with expiry.
"""

import logging
from typing import BinaryIO

from django.conf import settings

from media_assets.storage.base import StorageProvider

logger = logging.getLogger(__name__)


class R2StorageProvider(StorageProvider):
    """
    Cloudflare R2 storage backend (S3-compatible via boto3).

    Configuration (set in settings.py / .env):
        CLOUDFLARE_R2_ENDPOINT    — R2 account endpoint URL
        CLOUDFLARE_R2_ACCESS_KEY_ID
        CLOUDFLARE_R2_SECRET_ACCESS_KEY
        CLOUDFLARE_R2_BUCKET      — bucket name
        CLOUDFLARE_R2_CDN_URL     — CDN/custom domain base URL (e.g. https://cdn.bolayetu.com)
    """

    def __init__(self):
        self._client = None

    def _get_client(self):
        """Lazily initialise the boto3 S3 client."""
        if self._client is None:
            import boto3

            self._client = boto3.client(
                "s3",
                endpoint_url=settings.CLOUDFLARE_R2_ENDPOINT,
                aws_access_key_id=settings.CLOUDFLARE_R2_ACCESS_KEY_ID,
                aws_secret_access_key=settings.CLOUDFLARE_R2_SECRET_ACCESS_KEY,
                region_name=getattr(settings, "CLOUDFLARE_R2_REGION", "auto"),
            )
        return self._client

    @property
    def bucket(self) -> str:
        return settings.CLOUDFLARE_R2_BUCKET

    @property
    def cdn_base_url(self) -> str:
        return getattr(settings, "CLOUDFLARE_R2_CDN_URL", "").rstrip("/")

    def upload(
        self,
        *,
        file_obj: BinaryIO,
        object_key: str,
        content_type: str,
        public: bool = True,
    ) -> str:
        """
        Upload file to Cloudflare R2.

        Returns the CDN URL if cdn_base_url is configured,
        otherwise the direct R2 URL.
        """
        client = self._get_client()

        extra_args = {"ContentType": content_type}
        if public:
            extra_args["ACL"] = "public-read"

        client.upload_fileobj(
            file_obj,
            self.bucket,
            object_key,
            ExtraArgs=extra_args,
        )

        logger.info("Uploaded to R2: %s/%s", self.bucket, object_key)
        return self.get_public_url(object_key=object_key)

    def delete(self, *, object_key: str) -> None:
        """Delete an object from R2."""
        client = self._get_client()
        client.delete_object(Bucket=self.bucket, Key=object_key)
        logger.info("Deleted from R2: %s/%s", self.bucket, object_key)

    def exists(self, *, object_key: str) -> bool:
        """Check if an object exists in R2."""
        import botocore.exceptions

        client = self._get_client()
        try:
            client.head_object(Bucket=self.bucket, Key=object_key)
            return True
        except botocore.exceptions.ClientError as exc:
            if exc.response["Error"]["Code"] == "404":
                return False
            raise

    def generate_signed_url(self, *, object_key: str, expires_in: int = 3600) -> str:
        """Generate a pre-signed URL for private content."""
        client = self._get_client()
        return client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": object_key},
            ExpiresIn=expires_in,
        )

    def get_public_url(self, *, object_key: str) -> str:
        """Build the CDN/public URL for an object key."""
        if self.cdn_base_url:
            return f"{self.cdn_base_url}/{object_key}"
        # Fallback: direct R2 endpoint URL
        endpoint = settings.CLOUDFLARE_R2_ENDPOINT.rstrip("/")
        return f"{endpoint}/{self.bucket}/{object_key}"
