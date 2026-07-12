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


class PlayerDocumentCreateSerializer(serializers.Serializer):
    """
    Serializer for uploading a new player document.

    Accepts either a file upload (`document`) or a pre-existing DAM asset UUID (`asset`).
    """

    title = serializers.CharField(max_length=255)
    category = serializers.ChoiceField(choices=PlayerDocument.DocumentCategory.choices)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    document = serializers.FileField(required=False)
    asset = serializers.UUIDField(required=False)
    valid_from = serializers.DateField(required=False, allow_null=True)
    valid_until = serializers.DateField(required=False, allow_null=True)
    club = serializers.UUIDField(required=False, allow_null=True)
    is_private = serializers.BooleanField(required=False, default=False)

    def validate(self, data):
        document = data.get("document")
        asset_id = data.get("asset")

        if not document and not asset_id:
            raise serializers.ValidationError("Either document file or asset UUID is required.")

        if document and asset_id:
            raise serializers.ValidationError("Provide either document file or asset UUID, not both.")

        if asset_id:
            from media_assets.constants import AssetType
            from media_assets.models import MediaAsset

            try:
                asset = MediaAsset.objects.get(id=asset_id)
            except MediaAsset.DoesNotExist as exc:
                raise serializers.ValidationError({"asset": "Asset not found."}) from exc

            if asset.asset_type not in [AssetType.DOCUMENT, AssetType.PDF]:
                raise serializers.ValidationError({"asset": "Asset must be a document or PDF type."})

            data["asset_instance"] = asset

        return data


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
