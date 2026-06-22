from rest_framework import serializers
from .models import Advertisement


class AdvertisementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Advertisement
        fields = [
            'id',
            'title',
            'client_name',
            'image_url',
            'link_url',
            'placement',
            'status',
            'impressions',
            'clicks',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'impressions', 'clicks', 'created_at', 'updated_at']

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request.user, 'tenant') and request.user.tenant:
            validated_data['tenant'] = request.user.tenant
        return super().create(validated_data)

