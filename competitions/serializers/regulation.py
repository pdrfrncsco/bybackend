from rest_framework import serializers

from competitions.models import CompetitionRegulation
from competitions.services.regulation_service import CompetitionRegulationService


class CompetitionRegulationSerializer(serializers.ModelSerializer):
    document_url = serializers.SerializerMethodField()
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = CompetitionRegulation
        fields = [
            "id",
            "competition",
            "title",
            "summary",
            "version",
            "status",
            "status_label",
            "document_url",
            "published_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "competition",
            "status_label",
            "document_url",
            "published_at",
            "created_at",
            "updated_at",
        ]

    def get_document_url(self, obj: CompetitionRegulation) -> str:
        return CompetitionRegulationService.get_document_url(regulation=obj)


class CompetitionRegulationCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    summary = serializers.CharField(required=False, allow_blank=True, default="")
    version = serializers.CharField(max_length=32, required=False, default="1.0")
    status = serializers.ChoiceField(choices=CompetitionRegulation.Status.choices, required=False, default=CompetitionRegulation.Status.PUBLISHED)
    document = serializers.FileField()


class CompetitionRegulationUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, required=False)
    summary = serializers.CharField(required=False, allow_blank=True)
    version = serializers.CharField(max_length=32, required=False)
    status = serializers.ChoiceField(choices=CompetitionRegulation.Status.choices, required=False)
    document = serializers.FileField(required=False)
