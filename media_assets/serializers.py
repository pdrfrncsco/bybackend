"""
BOLAYETU — Media Asset Serializers
"""

from rest_framework import serializers

from media_assets.models import MediaAsset, MediaVariant, MediaUsage


class MediaVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaVariant
        fields = [
            "id",
            "variant_type",
            "cdn_url",
            "width",
            "height",
            "size_bytes",
            "mime_type",
        ]
        read_only_fields = fields


class MediaAssetSerializer(serializers.ModelSerializer):
    """Full serializer for MediaAsset (admin/detail views)."""

    variants = MediaVariantSerializer(many=True, read_only=True)
    public_url = serializers.CharField(read_only=True)

    class Meta:
        model = MediaAsset
        fields = [
            "id",
            "name",
            "asset_type",
            "category",
            "original_filename",
            "mime_type",
            "extension",
            "size_bytes",
            "width",
            "height",
            "cdn_url",
            "thumbnail_url",
            "public_url",
            "owner_type",
            "owner_id",
            "visibility",
            "status",
            "created_at",
            "updated_at",
            "variants",
        ]
        read_only_fields = fields


class MediaAssetListSerializer(serializers.ModelSerializer):
    """Compact serializer for list views."""

    public_url = serializers.CharField(read_only=True)

    class Meta:
        model = MediaAsset
        fields = [
            "id",
            "name",
            "asset_type",
            "category",
            "mime_type",
            "size_bytes",
            "thumbnail_url",
            "public_url",
            "status",
            "created_at",
        ]
        read_only_fields = fields


class MediaAssetUploadSerializer(serializers.Serializer):
    """Serializer for the upload endpoint (input only)."""

    file = serializers.ImageField(
        help_text="The file to upload. Supported: JPEG, PNG, WebP, GIF, SVG, PDF."
    )
    name = serializers.CharField(
        max_length=255,
        required=False,
        help_text="Optional human-readable name. Defaults to the original filename.",
    )
    category = serializers.CharField(
        max_length=30,
        required=False,
        help_text="Asset category (logo, banner, avatar, etc.).",
    )


class MediaUsageSerializer(serializers.ModelSerializer):
    """Serializer for MediaUsage — links asset to owner."""

    asset = MediaAssetListSerializer(read_only=True)

    class Meta:
        model = MediaUsage
        fields = [
            "id",
            "owner_type",
            "owner_id",
            "role",
            "order",
            "is_active",
            "asset",
            "created_at",
        ]
        read_only_fields = fields
