from rest_framework import serializers

from clubs.models import ClubSponsor


class ClubSponsorSerializer(serializers.ModelSerializer):
    sponsor_type_label = serializers.CharField(source="get_sponsor_type_display", read_only=True)
    logo_url = serializers.SerializerMethodField()
    uploaded_by_email = serializers.CharField(source="uploaded_by.email", read_only=True)

    class Meta:
        model = ClubSponsor
        fields = [
            "id",
            "club",
            "tenant",
            "name",
            "sponsor_type",
            "sponsor_type_label",
            "description",
            "website",
            "logo_asset",
            "logo_url",
            "uploaded_by",
            "uploaded_by_email",
            "is_active",
            "sort_order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "club",
            "tenant",
            "logo_asset",
            "logo_url",
            "uploaded_by",
            "uploaded_by_email",
            "created_at",
            "updated_at",
        ]

    def get_logo_url(self, obj: ClubSponsor) -> str:
        return obj.logo_asset.public_url if obj.logo_asset else ""


class ClubSponsorCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    sponsor_type = serializers.ChoiceField(choices=ClubSponsor.SponsorType.choices, default=ClubSponsor.SponsorType.PARTNER)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    website = serializers.URLField(required=False, allow_null=True, allow_blank=True)
    logo = serializers.FileField(required=False, allow_null=True)
    is_active = serializers.BooleanField(required=False, default=True)
    sort_order = serializers.IntegerField(required=False, default=0, min_value=0)


class ClubSponsorUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
    sponsor_type = serializers.ChoiceField(choices=ClubSponsor.SponsorType.choices, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    website = serializers.URLField(required=False, allow_null=True, allow_blank=True)
    logo = serializers.FileField(required=False, allow_null=True)
    is_active = serializers.BooleanField(required=False)
    sort_order = serializers.IntegerField(required=False, min_value=0)
