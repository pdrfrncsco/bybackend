from rest_framework import serializers
from .models import Referee, RefereeAvailability


class RefereeAvailabilitySerializer(serializers.ModelSerializer):
    referee = serializers.PrimaryKeyRelatedField(queryset=Referee.objects.all())

    class Meta:
        model = RefereeAvailability
        fields = ['id', 'referee', 'date', 'is_available', 'notes']
        read_only_fields = ['id']


class RefereeSerializer(serializers.ModelSerializer):
    tenant = serializers.UUIDField(source='tenant.id', read_only=True)
    availabilities = RefereeAvailabilitySerializer(many=True, read_only=True)

    class Meta:
        model = Referee
        fields = [
            'id',
            'tenant',
            'name',
            'bi',
            'category',
            'phone',
            'email',
            'is_active',
            'created_at',
            'updated_at',
            'availabilities',
        ]
        read_only_fields = ['id', 'tenant', 'created_at', 'updated_at']

    def validate_bi(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('O BI é obrigatório.')
        if len(value) < 5:
            raise serializers.ValidationError('O BI é demasiado curto.')
        return value

    def validate(self, attrs):
        name = attrs.get('name') or getattr(self.instance, 'name', '').strip()
        if not name:
            raise serializers.ValidationError({'name': 'O nome é obrigatório.'})
        return attrs
