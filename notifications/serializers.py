from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "type", "payload", "status", "created_at", "delivered_at"]
        read_only_fields = fields
