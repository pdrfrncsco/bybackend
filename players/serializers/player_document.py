"""
BOLAYETU — Player Document Serializers

Serializers for player document endpoints.
"""

from rest_framework import serializers

from players.models import PlayerDocument


class PlayerDocumentSerializer(serializers.ModelSerializer):
    """
    Serializer for viewing player documents.
    
    Used for: GET /api/v1/players/{slug}/documents/
    """
    
    category_label = serializers.SerializerMethodField()
    status_label = serializers.SerializerMethodField()
    asset_url = serializers.SerializerMethodField()
    club_name = serializers.CharField(source="club.name", read_only=True)
    uploaded_by_name = serializers.SerializerMethodField()
    verified_by_name = serializers.SerializerMethodField()
    is_valid = serializers.ReadOnlyField()
    
    class Meta:
        model = PlayerDocument
        fields = [
            "id",
            "title",
            "category",
            "category_label",
            "description",
            "asset_url",
            "status",
            "status_label",
            "valid_from",
            "valid_until",
            "is_valid",
            "club",
            "club_name",
            "is_private",
            "uploaded_by",
            "uploaded_by_name",
            "verified_by",
            "verified_by_name",
            "verified_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "uploaded_by",
            "verified_by",
            "verified_at",
            "created_at",
            "updated_at",
        ]
    
    def get_category_label(self, obj: PlayerDocument) -> str:
        return obj.get_category_display()
    
    def get_status_label(self, obj: PlayerDocument) -> str:
        return obj.get_status_display()
    
    def get_asset_url(self, obj: PlayerDocument) -> str | None:
        if obj.asset:
            return obj.asset.public_url
        return None
    
    def get_uploaded_by_name(self, obj: PlayerDocument) -> str | None:
        if obj.uploaded_by:
            return obj.uploaded_by.full_name
        return None
    
    def get_verified_by_name(self, obj: PlayerDocument) -> str | None:
        if obj.verified_by:
            return obj.verified_by.full_name
        return None


class PlayerDocumentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for uploading a new player document.
    
    Used for: POST /api/v1/players/{slug}/documents/
    """
    
    class Meta:
        model = PlayerDocument
        fields = [
            "title",
            "category",
            "description",
            "asset",
            "valid_from",
            "valid_until",
            "club",
            "is_private",
        ]
    
    def validate_asset(self, value):
        """Validate that the asset exists and is a document type."""
        if not value:
            raise serializers.ValidationError("Asset is required.")
        
        # Check if asset is a document type (not image/video)
        from media_assets.constants import AssetType
        if value.asset_type not in [AssetType.DOCUMENT, AssetType.PDF]:
            raise serializers.ValidationError(
                "Asset must be a document or PDF type."
            )
        
        return value


class PlayerDocumentUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating a player document.
    
    Used for: PATCH /api/v1/players/{slug}/documents/{id}/
    """
    
    class Meta:
        model = PlayerDocument
        fields = [
            "title",
            "category",
            "description",
            "valid_from",
            "valid_until",
            "is_private",
        ]


class PlayerDocumentVerifySerializer(serializers.Serializer):
    """
    Serializer for verifying a player document.
    
    Used for: POST /api/v1/players/{slug}/documents/{id}/verify/
    """
    
    pass  # No additional fields needed - verification is a simple action
