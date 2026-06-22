from rest_framework import serializers


class AdvertiseContactSerializer(serializers.Serializer):
    company_name = serializers.CharField(max_length=255)
    contact_name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=50, allow_blank=True)
    interest = serializers.CharField(max_length=255)
    message = serializers.CharField(allow_blank=True)


class SupportContactSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    subject = serializers.CharField(max_length=255)
    message = serializers.CharField()
