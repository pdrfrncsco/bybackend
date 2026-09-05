from rest_framework import serializers

from players.models import PlayerRegistrationRequest


class PlayerRegistrationRequestSerializer(serializers.ModelSerializer):
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    player_name = serializers.CharField(source="player.full_name", read_only=True)
    player_slug = serializers.CharField(source="player.slug", read_only=True)
    player_position_label = serializers.SerializerMethodField()
    club_name = serializers.CharField(source="club.name", read_only=True)
    club_slug = serializers.CharField(source="club.slug", read_only=True)
    competition_name = serializers.CharField(source="competition.name", read_only=True, allow_null=True)
    submitted_by_email = serializers.CharField(source="submitted_by.email", read_only=True)
    reviewed_by_email = serializers.CharField(source="reviewed_by.email", read_only=True)

    class Meta:
        model = PlayerRegistrationRequest
        fields = [
            "id",
            "player",
            "player_name",
            "player_slug",
            "player_position_label",
            "club",
            "club_name",
            "club_slug",
            "tenant",
            "competition",
            "competition_name",
            "submitted_by",
            "submitted_by_email",
            "joined_date",
            "shirt_number",
            "status",
            "status_label",
            "review_notes",
            "reviewed_by",
            "reviewed_by_email",
            "reviewed_at",
            "registration",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_player_position_label(self, obj: PlayerRegistrationRequest) -> str:
        from players.models import Player

        try:
            return Player.Position(obj.player.primary_position).label if obj.player.primary_position else ""
        except ValueError:
            return obj.player.primary_position or ""


class PlayerRegistrationRequestCreateSerializer(serializers.Serializer):
    club_id = serializers.UUIDField()
    joined_date = serializers.DateField()
    shirt_number = serializers.IntegerField(required=False, allow_null=True, min_value=1, max_value=99)
    competition_id = serializers.UUIDField(required=False, allow_null=True)


class PlayerRegistrationRequestReviewSerializer(serializers.Serializer):
    approve = serializers.BooleanField()
    review_notes = serializers.CharField(required=False, allow_blank=True, default="")


class PlayerRegistrationRequestDeclineSerializer(serializers.Serializer):
    review_notes = serializers.CharField(required=False, allow_blank=True, default="")
