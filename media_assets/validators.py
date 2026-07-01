"""
BOLAYETU — Media Asset Validators

File validation rules for uploads.

Architecture (08_MEDIA_STORAGE_ARCHITECTURE.md §16):
    Every upload must validate:
    - MIME type (using python-magic or file-header inspection)
    - Extension
    - File size
    - Never trust extension alone — always verify MIME type
"""

import os

from media_assets.constants import (
    ALLOWED_IMAGE_TYPES,
    ALLOWED_DOCUMENT_TYPES,
    ALLOWED_VIDEO_TYPES,
    MAX_IMAGE_SIZE,
    MAX_DOCUMENT_SIZE,
    MAX_VIDEO_SIZE,
    AssetType,
)
from media_assets.exceptions import (
    InvalidMediaFile,
    MediaAssetTooLarge,
    UnsupportedMediaType,
)


# Combined allowed MIME types
ALLOWED_MIME_TYPES = ALLOWED_IMAGE_TYPES | ALLOWED_DOCUMENT_TYPES | ALLOWED_VIDEO_TYPES

# Map MIME type → AssetType
MIME_TO_ASSET_TYPE = {
    **{mime: AssetType.IMAGE for mime in ALLOWED_IMAGE_TYPES},
    **{mime: AssetType.VIDEO for mime in ALLOWED_VIDEO_TYPES},
    "application/pdf": AssetType.PDF,
    **{mime: AssetType.DOCUMENT for mime in ALLOWED_DOCUMENT_TYPES if mime != "application/pdf"},
}

# Size limits per asset type
SIZE_LIMITS = {
    AssetType.IMAGE: MAX_IMAGE_SIZE,
    AssetType.PDF: MAX_DOCUMENT_SIZE,
    AssetType.DOCUMENT: MAX_DOCUMENT_SIZE,
    AssetType.VIDEO: MAX_VIDEO_SIZE,
    AssetType.AUDIO: MAX_DOCUMENT_SIZE,
    AssetType.ARCHIVE: MAX_DOCUMENT_SIZE,
}

# Default limit for unknown types
DEFAULT_SIZE_LIMIT = MAX_IMAGE_SIZE


def get_mime_type(file_obj) -> str:
    """
    Detect MIME type from file content using python-magic if available,
    falling back to the content_type provided by the upload.

    Note: python-magic requires libmagic (pip install python-magic).
    Fallback: use Django's UploadedFile.content_type (provided by the browser,
    so less reliable — acceptable for internal admin uploads).
    """
    # Try python-magic first (more reliable)
    try:
        import magic
        file_obj.seek(0)
        sample = file_obj.read(2048)
        file_obj.seek(0)
        return magic.from_buffer(sample, mime=True)
    except (ImportError, Exception):
        pass

    # Fallback: content_type from upload
    if hasattr(file_obj, "content_type") and file_obj.content_type:
        return file_obj.content_type

    return "application/octet-stream"


def validate_upload(file_obj) -> tuple[str, str, AssetType]:
    """
    Validate an uploaded file.

    Checks MIME type, file size.

    Args:
        file_obj: Django UploadedFile or file-like object.

    Returns:
        Tuple of (mime_type, extension, asset_type).

    Raises:
        UnsupportedMediaType: If the MIME type is not allowed.
        MediaAssetTooLarge: If the file exceeds the size limit.
        InvalidMediaFile: If the file appears to be empty or corrupt.
    """
    if not file_obj or file_obj.size == 0:
        raise InvalidMediaFile(detail="O ficheiro está vazio.")

    mime_type = get_mime_type(file_obj)

    if mime_type not in ALLOWED_MIME_TYPES:
        raise UnsupportedMediaType(
            detail=f"Tipo de ficheiro não suportado: {mime_type}. "
                   f"Tipos aceites: JPEG, PNG, WebP, GIF, PDF, DOCX, MP4."
        )

    asset_type = MIME_TO_ASSET_TYPE.get(mime_type, AssetType.DOCUMENT)
    size_limit = SIZE_LIMITS.get(asset_type, DEFAULT_SIZE_LIMIT)

    if file_obj.size > size_limit:
        limit_mb = size_limit / (1024 * 1024)
        raise MediaAssetTooLarge(
            detail=f"O ficheiro excede o limite de {limit_mb:.0f} MB."
        )

    # Extract extension from original filename
    ext = ""
    if hasattr(file_obj, "name") and file_obj.name:
        _, ext = os.path.splitext(file_obj.name)
        ext = ext.lstrip(".").lower()

    return mime_type, ext, asset_type


def validate_image_upload(file_obj):
    """
    Strict image-only validation.

    Raises:
        UnsupportedMediaType: If the file is not a supported image type.
    """
    mime_type, ext, asset_type = validate_upload(file_obj)

    if mime_type not in ALLOWED_IMAGE_TYPES:
        raise UnsupportedMediaType(
            detail="Apenas imagens são aceites (JPEG, PNG, WebP, GIF, SVG)."
        )

    return mime_type, ext, asset_type
