"""
BOLAYETU — Cloudflare R2 Storage Backends
Skill: BOLAYETU_CLOUDFLARE_SKILL

FORBIDDEN: MEDIA_ROOT, local storage, /media/ paths
REQUIRED:  All files → Cloudflare R2 → served via cdn.bolayetu.com

Storage classes:
- R2PublicStorage   → photos, logos, banners (public, long cache)
- R2PrivateStorage  → documents, contracts (requires signed URLs)

File URL format:
    https://cdn.bolayetu.com/players/{uuid}/photo/photo.webp
    https://cdn.bolayetu.com/clubs/{uuid}/logo/badge.webp
    https://cdn.bolayetu.com/tenants/{slug}/logo/logo.webp

NEVER expose:
    https://{account-id}.r2.cloudflarestorage.com/...  ← forbidden
    /media/players/photo.jpg                            ← forbidden
"""

import os
import uuid
import mimetypes
from pathlib import PurePosixPath
from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings


# ===================================================================
# UPLOAD PATH HELPERS
# Consistent R2 key structure for all media types
# ===================================================================

def player_photo_upload_path(instance, filename: str) -> str:
    """players/{player_id}/photo/{uuid}.{ext}"""
    ext = PurePosixPath(filename).suffix.lower()
    return f'players/{instance.id}/photo/{uuid.uuid4()}{ext}'


def player_video_upload_path(instance, filename: str) -> str:
    """players/{player_id}/videos/{uuid}.{ext}"""
    ext = PurePosixPath(filename).suffix.lower()
    return f'players/{instance.player_id}/videos/{uuid.uuid4()}{ext}'


def player_document_upload_path(instance, filename: str) -> str:
    """players/{player_id}/documents/{uuid}.{ext}"""
    ext = PurePosixPath(filename).suffix.lower()
    return f'players/{instance.player_id}/documents/{uuid.uuid4()}{ext}'


def club_logo_upload_path(instance, filename: str) -> str:
    """clubs/{club_id}/logo/{uuid}.{ext}"""
    ext = PurePosixPath(filename).suffix.lower()
    return f'clubs/{instance.id}/logo/{uuid.uuid4()}{ext}'


def club_banner_upload_path(instance, filename: str) -> str:
    """clubs/{club_id}/banner/{uuid}.{ext}"""
    ext = PurePosixPath(filename).suffix.lower()
    return f'clubs/{instance.id}/banner/{uuid.uuid4()}{ext}'


def club_document_upload_path(instance, filename: str) -> str:
    """clubs/{club_id}/documents/{uuid}.{ext}"""
    ext = PurePosixPath(filename).suffix.lower()
    return f'clubs/{instance.club_id}/documents/{uuid.uuid4()}{ext}'


def tenant_logo_upload_path(instance, filename: str) -> str:
    """tenants/logos/{slug}/{uuid}.{ext}"""
    ext = PurePosixPath(filename).suffix.lower()
    return f'tenants/logos/{instance.slug}/{uuid.uuid4()}{ext}'


def user_avatar_upload_path(instance, filename: str) -> str:
    """users/{user_id}/avatar/{uuid}.{ext}"""
    ext = PurePosixPath(filename).suffix.lower()
    return f'users/{instance.id}/avatar/{uuid.uuid4()}{ext}'


def news_image_upload_path(instance, filename: str) -> str:
    """news/{article_id}/images/{uuid}.{ext}"""
    ext = PurePosixPath(filename).suffix.lower()
    return f'news/{instance.id}/images/{uuid.uuid4()}{ext}'


def stadium_photo_upload_path(instance, filename: str) -> str:
    """stadiums/{stadium_id}/photos/{uuid}.{ext}"""
    ext = PurePosixPath(filename).suffix.lower()
    return f'stadiums/{instance.id}/photos/{uuid.uuid4()}{ext}'


# ===================================================================
# R2 STORAGE BACKENDS
# ===================================================================

class R2PublicStorage(S3Boto3Storage):
    """
    Cloudflare R2 storage for PUBLIC files.
    Photos, logos, banners — no auth required.
    Files served via cdn.bolayetu.com with 1-year cache.

    URL format: https://cdn.bolayetu.com/{key}
    """
    access_key = settings.AWS_ACCESS_KEY_ID
    secret_key = settings.AWS_SECRET_ACCESS_KEY
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    endpoint_url = settings.AWS_S3_ENDPOINT_URL
    custom_domain = getattr(settings, 'AWS_S3_CUSTOM_DOMAIN', 'cdn.bolayetu.com')

    # Public files — no query string auth
    querystring_auth = False
    file_overwrite = False
    default_acl = None

    # Aggressive caching for public media (1 year)
    object_parameters = {
        'CacheControl': 'max-age=31536000, s-maxage=31536000, public',
    }

    def url(self, name):
        """Always return CDN URL, never raw R2 bucket URL."""
        if self.custom_domain:
            return f'https://{self.custom_domain}/{name}'
        return super().url(name)


class R2PrivateStorage(S3Boto3Storage):
    """
    Cloudflare R2 storage for PRIVATE files.
    Documents, contracts, medical records — requires signed URLs.

    URL format: Presigned R2 URL (expires in 1 hour)
    """
    access_key = settings.AWS_ACCESS_KEY_ID
    secret_key = settings.AWS_SECRET_ACCESS_KEY
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    endpoint_url = settings.AWS_S3_ENDPOINT_URL

    # Signed URLs — authentication required
    querystring_auth = True
    querystring_expire = 3600  # 1 hour
    file_overwrite = False
    default_acl = None
    signature_version = 's3v4'

    def get_presigned_url(self, name: str, expiration: int = 3600) -> str:
        """
        Generate a presigned URL for temporary private file access.

        Args:
            name:       The file key in R2 (e.g. 'players/uuid/documents/contract.pdf')
            expiration: URL validity in seconds (default: 1 hour)

        Returns:
            Presigned URL string
        """
        client = self.connection.meta.client
        return client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': self.bucket_name,
                'Key': name,
            },
            ExpiresIn=expiration,
        )


# ===================================================================
# UPLOAD VALIDATORS
# ===================================================================

ALLOWED_IMAGE_TYPES = {
    'image/jpeg', 'image/png', 'image/webp', 'image/gif', 'image/svg+xml'
}

ALLOWED_VIDEO_TYPES = {
    'video/mp4', 'video/webm', 'video/quicktime', 'video/x-msvideo'
}

ALLOWED_DOCUMENT_TYPES = {
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
}

MAX_IMAGE_SIZE = 10 * 1024 * 1024   # 10 MB
MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500 MB
MAX_DOC_SIZE = 25 * 1024 * 1024     # 25 MB


def validate_image_upload(file):
    """Validate uploaded image file."""
    from django.core.exceptions import ValidationError

    mime_type, _ = mimetypes.guess_type(file.name)
    if mime_type not in ALLOWED_IMAGE_TYPES:
        raise ValidationError(
            f'File type {mime_type} is not allowed. '
            f'Allowed types: {", ".join(ALLOWED_IMAGE_TYPES)}'
        )
    if file.size > MAX_IMAGE_SIZE:
        raise ValidationError(
            f'Image size {file.size / 1024 / 1024:.1f}MB exceeds the '
            f'{MAX_IMAGE_SIZE / 1024 / 1024:.0f}MB limit.'
        )


def validate_video_upload(file):
    """Validate uploaded video file."""
    from django.core.exceptions import ValidationError

    mime_type, _ = mimetypes.guess_type(file.name)
    if mime_type not in ALLOWED_VIDEO_TYPES:
        raise ValidationError(
            f'File type {mime_type} is not allowed. '
            f'Allowed video types: {", ".join(ALLOWED_VIDEO_TYPES)}'
        )
    if file.size > MAX_VIDEO_SIZE:
        raise ValidationError(
            f'Video size {file.size / 1024 / 1024:.0f}MB exceeds the '
            f'{MAX_VIDEO_SIZE / 1024 / 1024:.0f}MB limit.'
        )


def validate_document_upload(file):
    """Validate uploaded document file."""
    from django.core.exceptions import ValidationError

    mime_type, _ = mimetypes.guess_type(file.name)
    if mime_type not in ALLOWED_DOCUMENT_TYPES:
        raise ValidationError(
            f'File type {mime_type} is not allowed. '
            f'Allowed document types: PDF, DOC, DOCX'
        )
    if file.size > MAX_DOC_SIZE:
        raise ValidationError(
            f'Document size {file.size / 1024 / 1024:.1f}MB exceeds the '
            f'{MAX_DOC_SIZE / 1024 / 1024:.0f}MB limit.'
        )
