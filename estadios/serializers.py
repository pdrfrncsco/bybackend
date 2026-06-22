from rest_framework import serializers
from .models import Stadium

class StadiumSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stadium
        fields = ['id', 'name', 'location', 'capacity', 'image', 'created_at']
        read_only_fields = ['id', 'created_at', 'tenant']
