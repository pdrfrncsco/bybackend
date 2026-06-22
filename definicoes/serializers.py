from rest_framework import serializers
from .models import TenantSettings


class TenantSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantSettings
        fields = [
            'id',
            'email_alerts',
            'match_updates',
            'marketing',
            'financial_reports',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

