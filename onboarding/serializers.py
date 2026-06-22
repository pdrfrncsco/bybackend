from rest_framework import serializers
from .models import OnboardingRequest
from core.models import Tenant

class OnboardingRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnboardingRequest
        fields = [
            'id', 'organization_name', 'organization_slug', 'organization_type',
            'country', 'primary_color', 'logo', 'season_name', 'status',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'status']

    def validate_organization_slug(self, value):
        if Tenant.objects.filter(slug=value).exists():
            raise serializers.ValidationError("Este slug já está em uso.")
        return value

    def create(self, validated_data):
        # Ensure slug is unique or handle uniqueness logic if needed
        return super().create(validated_data)
