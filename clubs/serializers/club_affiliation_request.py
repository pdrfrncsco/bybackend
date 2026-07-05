from rest_framework import serializers

from clubs.models import ClubAffiliationRequest


class ClubAffiliationRequestSerializer(serializers.ModelSerializer):
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    reviewed_by_email = serializers.CharField(source="reviewed_by.email", read_only=True)
    submitted_by_email = serializers.CharField(source="submitted_by.email", read_only=True)

    class Meta:
        model = ClubAffiliationRequest
        fields = [
            "id",
            "tenant",
            "submitted_by",
            "submitted_by_email",
            "name",
            "short_name",
            "founded_year",
            "city",
            "country",
            "email",
            "phone",
            "website",
            "description",
            "primary_color",
            "secondary_color",
            "stadium_name",
            "stadium_capacity",
            "status",
            "status_label",
            "review_notes",
            "reviewed_by",
            "reviewed_by_email",
            "reviewed_at",
            "club",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "tenant",
            "submitted_by",
            "submitted_by_email",
            "status",
            "status_label",
            "review_notes",
            "reviewed_by",
            "reviewed_by_email",
            "reviewed_at",
            "club",
            "created_at",
            "updated_at",
        ]


class ClubAffiliationRequestCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    short_name = serializers.CharField(max_length=50, required=False, allow_blank=True, default="")
    founded_year = serializers.IntegerField(required=False, allow_null=True)
    city = serializers.CharField(max_length=255, required=False, allow_null=True, allow_blank=True)
    country = serializers.CharField(max_length=100, required=False, default="Angola")
    email = serializers.EmailField(required=False, allow_null=True, allow_blank=True)
    phone = serializers.CharField(max_length=20, required=False, allow_null=True, allow_blank=True)
    website = serializers.URLField(required=False, allow_null=True, allow_blank=True)
    description = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    primary_color = serializers.CharField(max_length=7, required=False, default="#014D40")
    secondary_color = serializers.CharField(max_length=7, required=False, default="#94D3C1")
    stadium_name = serializers.CharField(max_length=255, required=False, allow_null=True, allow_blank=True)
    stadium_capacity = serializers.IntegerField(required=False, allow_null=True)


class ClubAffiliationRequestReviewSerializer(serializers.Serializer):
    approve = serializers.BooleanField()
    review_notes = serializers.CharField(required=False, allow_blank=True, default="")
