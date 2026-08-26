from rest_framework import serializers

from clubs.models import ClubDocument


class ClubDocumentSerializer(serializers.ModelSerializer):
    category_label = serializers.CharField(source="get_category_display", read_only=True)
    asset_url = serializers.SerializerMethodField()
    uploaded_by_email = serializers.CharField(source="uploaded_by.email", read_only=True)

    class Meta:
        model = ClubDocument
        fields = [
            "id",
            "club",
            "tenant",
            "title",
            "category",
            "category_label",
            "description",
            "asset",
            "asset_url",
            "uploaded_by",
            "uploaded_by_email",
            "is_public",
            "valid_until",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "club",
            "tenant",
            "asset",
            "asset_url",
            "uploaded_by",
            "uploaded_by_email",
            "created_at",
            "updated_at",
        ]

    def get_asset_url(self, obj: ClubDocument) -> str:
        return obj.asset.public_url if obj.asset else ""


class ClubDocumentCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    category = serializers.ChoiceField(choices=ClubDocument.Category.choices, default=ClubDocument.Category.OTHER)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    document = serializers.FileField(required=False)
    asset = serializers.UUIDField(required=False)

    def validate(self, data):
        if not data.get("document") and not data.get("asset"):
            raise serializers.ValidationError("Provide either document file or asset UUID.")
        if data.get("document") and data.get("asset"):
            raise serializers.ValidationError("Provide either document file or asset UUID, not both.")
        return data
    is_public = serializers.BooleanField(required=False, default=False)
    valid_until = serializers.DateField(required=False, allow_null=True)

