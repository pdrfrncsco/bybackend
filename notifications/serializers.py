from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    timestamp = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'type', 'timestamp', 'read', 'link']
        read_only_fields = ['id', 'timestamp', 'created_at', 'updated_at']
