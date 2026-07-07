"""
BOLAYETU — Transfer Serializers

Serializers for Transfer endpoints.
"""

from rest_framework import serializers

from transfers.models import Transfer


class TransferSerializer(serializers.ModelSerializer):
    """
    Public transfer serializer.

    Used for: GET /api/v1/transfers/ (list), GET /api/v1/transfers/{id}/ (detail)
    """

    status_label = serializers.SerializerMethodField()
    player_name = serializers.CharField(source="player.full_name", read_only=True)
    player_slug = serializers.CharField(source="player.slug", read_only=True)
    from_club_name = serializers.SerializerMethodField()
    to_club_name = serializers.CharField(source="to_club.name", read_only=True)

    class Meta:
        model = Transfer
        fields = [
            "id",
            "player",
            "player_name",
            "player_slug",
            "from_club",
            "from_club_name",
            "to_club",
            "to_club_name",
            "competition",
            "joined_date",
            "shirt_number",
            "fee",
            "status",
            "status_label",
            "request_date",
            "completed_date",
            "rejection_reason",
        ]
        read_only_fields = fields

    def get_status_label(self, obj: Transfer) -> str:
        return obj.get_status_display()

    def get_from_club_name(self, obj: Transfer) -> str | None:
        return obj.from_club.name if obj.from_club else "Free Agent"


class TransferDetailSerializer(serializers.ModelSerializer):
    """
    Extended transfer serializer with full details.

    Includes nested player and club information.
    """

    status_label = serializers.SerializerMethodField()
    player = serializers.SerializerMethodField()
    from_club = serializers.SerializerMethodField()
    to_club = serializers.SerializerMethodField()
    competition = serializers.SerializerMethodField()

    class Meta:
        model = Transfer
        fields = [
            "id",
            "player",
            "from_club",
            "to_club",
            "competition",
            "joined_date",
            "shirt_number",
            "fee",
            "status",
            "status_label",
            "request_date",
            "completed_date",
            "rejection_reason",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_status_label(self, obj: Transfer) -> str:
        return obj.get_status_display()

    def get_player(self, obj: Transfer) -> dict:
        if not obj.player:
            return None
        return {
            "id": obj.player.id,
            "slug": obj.player.slug,
            "full_name": obj.player.full_name,
            "primary_position": obj.player.primary_position,
            "nationality": obj.player.nationality,
        }

    def get_from_club(self, obj: Transfer) -> dict | None:
        if not obj.from_club:
            return {"name": "Free Agent", "id": None}
        return {
            "id": obj.from_club.id,
            "name": obj.from_club.name,
            "slug": obj.from_club.slug,
        }

    def get_to_club(self, obj: Transfer) -> dict:
        return {
            "id": obj.to_club.id,
            "name": obj.to_club.name,
            "slug": obj.to_club.slug,
        }

    def get_competition(self, obj: Transfer) -> dict | None:
        if not obj.competition:
            return None
        return {
            "id": obj.competition.id,
            "name": obj.competition.name,
        }


class TransferCreateSerializer(serializers.Serializer):
    """
    Serializer for creating a new transfer request.

    Required fields:
        - player_id: ID of the player to transfer
        - to_club_id: ID of the destination club
        - joined_date: Date the player will join the new club

    Optional fields:
        - from_club_id: ID of the origin club (if None, assumes free agent)
        - competition_id: Competition for the new registration
        - shirt_number: Shirt number at new club
        - fee: Transfer fee amount
    """

    player_id = serializers.UUIDField(help_text="ID of the player to transfer")
    to_club_id = serializers.UUIDField(help_text="ID of the destination club")
    joined_date = serializers.DateField(help_text="Date the player will join the new club")
    from_club_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text="ID of the origin club (omit for free agent transfer)"
    )
    competition_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text="Competition for the new registration"
    )
    shirt_number = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=1,
        max_value=99,
        help_text="Shirt number at new club"
    )
    fee = serializers.DecimalField(
        required=False,
        allow_null=True,
        max_digits=12,
        decimal_places=2,
        help_text="Transfer fee amount"
    )


class TransferApprovalSerializer(serializers.Serializer):
    """Serializer for approving a transfer (no additional fields needed)."""

    pass


class TransferRejectionSerializer(serializers.Serializer):
    """Serializer for rejecting a transfer with a reason."""

    rejection_reason = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500,
        help_text="Reason for rejecting the transfer"
    )
