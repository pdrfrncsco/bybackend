from rest_framework import serializers
from core.models import Tenant


class OrganizationSerializer(serializers.ModelSerializer):
    logoUrl = serializers.SerializerMethodField()

    class Meta:
        model = Tenant
        fields = (
            'id',
            'name',
            'slug',
            'type',
            'logo',
            'logoUrl',
            'primary_color',
            'secondary_color',
            'country',
            'location',
            'email',
            'phone',
            'website',
            'description',
            'is_public',
            'verified',
        )
        extra_kwargs = {
            'logo': {'write_only': True, 'required': False, 'allow_null': True},
        }

    def get_logoUrl(self, obj):
        request = self.context.get('request')
        if obj.logo and hasattr(obj.logo, 'url'):
            if request is not None:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return ''


class PublicOrganizationSerializer(OrganizationSerializer):
    activeTournaments = serializers.IntegerField(read_only=True)
    totalClubs = serializers.IntegerField(read_only=True)
    last_activity = serializers.DateTimeField(read_only=True)

    class Meta(OrganizationSerializer.Meta):
        fields = OrganizationSerializer.Meta.fields + (
            'activeTournaments',
            'totalClubs',
            'last_activity',
        )


class OrganizationHistoryEntrySerializer(serializers.Serializer):
    season = serializers.CharField()
    tournament_name = serializers.CharField()
    tournament_id = serializers.CharField(allow_blank=True, required=False)
    tournament_format = serializers.CharField(allow_blank=True, required=False)
    winner_club_name = serializers.CharField(allow_blank=True)
    runner_up_club_name = serializers.CharField(allow_blank=True, required=False)
    winner_club_id = serializers.CharField(allow_blank=True, required=False)
    runner_up_club_id = serializers.CharField(allow_blank=True, required=False)
