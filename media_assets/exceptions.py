"""
BOLAYETU — Media Asset Exceptions

Domain exceptions for the DAM module.
All exceptions inherit from DRF's APIException so they are caught
by the global custom_exception_handler and converted to the standard
error envelope.
"""

from rest_framework import status
from rest_framework.exceptions import APIException


class MediaAssetException(APIException):
    """Base exception for all media_assets domain errors."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Ocorreu um erro no asset."
    default_code = "media_asset_error"


class MediaAssetNotFound(MediaAssetException):
    """Raised when a MediaAsset cannot be found."""

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Asset não encontrado."
    default_code = "media_asset_not_found"


class MediaAssetUploadFailed(MediaAssetException):
    """Raised when a file upload to storage fails."""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Falha no upload do ficheiro."
    default_code = "media_asset_upload_failed"


class InvalidMediaFile(MediaAssetException):
    """Raised when the uploaded file fails validation."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Ficheiro inválido."
    default_code = "invalid_media_file"


class MediaAssetTooLarge(MediaAssetException):
    """Raised when the uploaded file exceeds the size limit."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Ficheiro demasiado grande."
    default_code = "media_asset_too_large"


class UnsupportedMediaType(MediaAssetException):
    """Raised when the file MIME type is not supported."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Tipo de ficheiro não suportado."
    default_code = "unsupported_media_type"


class MediaAssetNotReady(MediaAssetException):
    """Raised when trying to use an asset that is not yet ready."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = "Asset ainda não está disponível."
    default_code = "media_asset_not_ready"


class MediaUsageNotFound(MediaAssetException):
    """Raised when a MediaUsage record cannot be found."""

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Ligação de asset não encontrada."
    default_code = "media_usage_not_found"
