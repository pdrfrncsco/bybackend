"""
BOLAYETU — Media Asset Constants

Defines all enumerations and constants for the DAM module.
"""

from django.db import models


class AssetType(models.TextChoices):
    IMAGE = "image", "Imagem"
    VIDEO = "video", "Vídeo"
    DOCUMENT = "document", "Documento"
    AUDIO = "audio", "Áudio"
    PDF = "pdf", "PDF"
    ARCHIVE = "archive", "Arquivo"


class AssetCategory(models.TextChoices):
    AVATAR = "avatar", "Avatar"
    LOGO = "logo", "Logótipo"
    BANNER = "banner", "Banner"
    COVER = "cover", "Capa"
    GALLERY = "gallery", "Galeria"
    VIDEO = "video", "Vídeo"
    DOCUMENT = "document", "Documento"
    CERTIFICATE = "certificate", "Certificado"
    REPORT = "report", "Relatório"
    EXPORT = "export", "Exportação"
    NEWS_IMAGE = "news_image", "Imagem de Notícia"
    SPONSOR_LOGO = "sponsor_logo", "Logótipo de Patrocinador"


class AssetVisibility(models.TextChoices):
    PUBLIC = "public", "Público"
    INTERNAL = "internal", "Interno"
    PRIVATE = "private", "Privado"
    SIGNED = "signed", "Assinado (URL temporário)"


class AssetStatus(models.TextChoices):
    UPLOADING = "uploading", "A fazer upload"
    PROCESSING = "processing", "A processar"
    READY = "ready", "Pronto"
    ARCHIVED = "archived", "Arquivado"
    DELETED = "deleted", "Eliminado"


class AssetVariantType(models.TextChoices):
    ORIGINAL = "original", "Original"
    THUMBNAIL = "thumbnail", "Thumbnail"
    SMALL = "small", "Pequeno"
    MEDIUM = "medium", "Médio"
    LARGE = "large", "Grande"
    WEBP = "webp", "WebP"
    AVIF = "avif", "AVIF"


class OwnerType(models.TextChoices):
    ORGANIZATION = "organization", "Organização"
    CLUB = "club", "Clube"
    COMPETITION = "competition", "Competição"
    MATCH = "match", "Jogo"
    NEWS = "news", "Notícia"
    PLAYER = "player", "Jogador"
    SYSTEM = "system", "Sistema"


# Allowed MIME types per asset type
ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/avif",
    "image/svg+xml",
}

ALLOWED_DOCUMENT_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}

ALLOWED_VIDEO_TYPES = {
    "video/mp4",
    "video/mpeg",
    "video/quicktime",
    "video/x-msvideo",
    "video/webm",
}

# File size limits (in bytes)
MAX_IMAGE_SIZE = 10 * 1024 * 1024       # 10 MB
MAX_DOCUMENT_SIZE = 50 * 1024 * 1024    # 50 MB
MAX_VIDEO_SIZE = 500 * 1024 * 1024      # 500 MB

# Thumbnail dimensions
THUMBNAIL_SIZES = {
    AssetVariantType.THUMBNAIL: (150, 150),
    AssetVariantType.SMALL: (320, 240),
    AssetVariantType.MEDIUM: (640, 480),
    AssetVariantType.LARGE: (1280, 960),
}
