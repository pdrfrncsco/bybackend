from rest_framework import serializers

from .models import ReportJob


class ReportDefinitionSerializer(serializers.Serializer):
    id = serializers.CharField()
    label = serializers.CharField()
    description = serializers.CharField()
    requires = serializers.ListField(
        child=serializers.CharField(),
    )
    supported_formats = serializers.ListField(
        child=serializers.CharField(),
    )
    required_plan = serializers.CharField()


class ReportJobSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = ReportJob
        fields = [
            "id",
            "report_type",
            "format",
            "status",
            "params",
            "file_url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "file_url",
            "created_at",
            "updated_at",
        ]

    def get_file_url(self, obj):
        request = self.context.get("request")
        if not obj.file:
            return None
        if request:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url


class GenerateReportSerializer(serializers.Serializer):
    report_type = serializers.ChoiceField(choices=[choice[0] for choice in ReportJob.REPORT_TYPE_CHOICES])
    format = serializers.ChoiceField(choices=[choice[0] for choice in ReportJob.FORMAT_CHOICES])
    params = serializers.DictField(child=serializers.CharField(), required=False)
