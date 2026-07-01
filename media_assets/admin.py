"""
BOLAYETU — Media Assets Django Admin
"""

from django.contrib import admin

from media_assets.models import MediaAsset, MediaUsage, MediaVariant


class MediaVariantInline(admin.TabularInline):
    model = MediaVariant
    extra = 0
    readonly_fields = ["variant_type", "cdn_url", "width", "height", "size_bytes", "mime_type"]
    can_delete = False


class MediaUsageInline(admin.TabularInline):
    model = MediaUsage
    extra = 0
    readonly_fields = ["owner_type", "owner_id", "role", "is_active", "created_at"]
    can_delete = False


@admin.register(MediaAsset)
class MediaAssetAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "asset_type",
        "category",
        "owner_type",
        "mime_type",
        "size_bytes",
        "status",
        "visibility",
        "tenant",
        "created_at",
    ]
    list_filter = ["asset_type", "category", "status", "visibility", "owner_type"]
    search_fields = ["name", "original_filename", "object_key"]
    readonly_fields = [
        "id",
        "checksum_sha256",
        "object_key",
        "cdn_url",
        "private_url",
        "thumbnail_url",
        "size_bytes",
        "mime_type",
        "extension",
        "width",
        "height",
        "created_at",
        "updated_at",
    ]
    inlines = [MediaVariantInline, MediaUsageInline]


@admin.register(MediaUsage)
class MediaUsageAdmin(admin.ModelAdmin):
    list_display = ["owner_type", "owner_id", "role", "is_active", "asset", "created_at"]
    list_filter = ["owner_type", "role", "is_active"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(MediaVariant)
class MediaVariantAdmin(admin.ModelAdmin):
    list_display = ["asset", "variant_type", "width", "height", "size_bytes", "created_at"]
    list_filter = ["variant_type"]
    readonly_fields = ["created_at", "updated_at"]
