from rest_framework import serializers
from players.models import PlayerIdentityDocument


class PlayerIdentityDocumentSerializer(serializers.ModelSerializer):
    issuing_country_label = serializers.SerializerMethodField()

    class Meta:
        model = PlayerIdentityDocument
        fields = [
            "id",
            "document_type",
            "document_number",
            "issuing_country",
            "issuing_country_label",
            "issuing_authority",
            "issue_date",
            "expiry_date",
            "document_front",
            "document_back",
            "verification_status",
            "verified_by",
            "verified_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "verification_status", "verified_by", "verified_at", "created_at", "updated_at"]

    def get_issuing_country_label(self, obj: PlayerIdentityDocument) -> str | None:
        if obj.issuing_country:
            return obj.issuing_country
        return None


class PlayerIdentityDocumentCreateSerializer(serializers.Serializer):
    document_type = serializers.ChoiceField(choices=PlayerIdentityDocument._meta.get_field("document_type").choices)
    document_number = serializers.CharField(max_length=128)
    issuing_country = serializers.CharField(max_length=3, required=False, allow_blank=True)
    issuing_authority = serializers.CharField(max_length=255, required=False, allow_blank=True)
    issue_date = serializers.DateField(required=False, allow_null=True)
    expiry_date = serializers.DateField(required=False, allow_null=True)
    document = serializers.FileField(required=False)
    asset = serializers.UUIDField(required=False)

    def validate(self, data):
        doc = data.get("document")
        asset_id = data.get("asset")
        if not doc and not asset_id:
            raise serializers.ValidationError("Either document file or asset UUID is required.")
        if doc and asset_id:
            raise serializers.ValidationError("Provide either document file or asset UUID, not both.")

        if asset_id:
            from media_assets.models import MediaAsset
            try:
                asset = MediaAsset.objects.get(id=asset_id)
            except MediaAsset.DoesNotExist as exc:
                raise serializers.ValidationError({"asset": "Asset not found."}) from exc
            data["asset_instance"] = asset
        return data


class PlayerIdentityDocumentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerIdentityDocument
        fields = [
            "document_type",
            "document_number",
            "issuing_country",
            "issuing_authority",
            "issue_date",
            "expiry_date",
        ]
