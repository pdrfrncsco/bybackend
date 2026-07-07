"""
BOLAYETU — Transfer Serializers

DRF serializers for player transfers including permanent, loans, and free agents.
"""

from rest_framework import serializers
from datetime import date

from players.models import Player
from clubs.models import Club, Transfer


class TransferPlayerSerializer(serializers.ModelSerializer):
    """Basic player info in transfer."""

    class Meta:
        model = Player
        fields = ['id', 'full_name', 'primary_position', 'date_of_birth']
        read_only_fields = fields


class TransferClubSerializer(serializers.ModelSerializer):
    """Basic club info in transfer."""

    class Meta:
        model = Club
        fields = ['id', 'name', 'slug']
        read_only_fields = fields


class TransferSerializer(serializers.ModelSerializer):
    """Complete transfer details."""

    player = TransferPlayerSerializer(read_only=True)
    from_club = TransferClubSerializer(read_only=True)
    to_club = TransferClubSerializer(read_only=True)
    transfer_type_display = serializers.CharField(
        source='get_transfer_type_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )

    class Meta:
        model = Transfer
        fields = [
            'id', 'player', 'from_club', 'to_club',
            'transfer_type', 'transfer_type_display',
            'transfer_date', 'status', 'status_display',
            'loan_end_date', 'loan_return_mandatory',
            'fee', 'salary_contribution',
            'approved_at', 'completed_at', 'cancelled_at',
            'notes', 'created_at'
        ]
        read_only_fields = [
            'id', 'player', 'from_club', 'to_club',
            'approved_at', 'completed_at', 'cancelled_at',
            'created_at'
        ]


class TransferCreateSerializer(serializers.Serializer):
    """Serializer for creating transfers."""

    player_id = serializers.UUIDField()
    to_club_id = serializers.UUIDField()
    from_club_id = serializers.UUIDField(required=False, allow_null=True)
    transfer_type = serializers.ChoiceField(
        choices=['permanent', 'loan', 'free_agent'],
        default='permanent'
    )
    transfer_date = serializers.DateField()
    loan_end_date = serializers.DateField(required=False, allow_null=True)
    salary_contribution = serializers.BooleanField(default=False)
    fee = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        required=False,
        allow_null=True
    )
    notes = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True
    )

    def validate(self, data):
        """Validate transfer data."""
        transfer_type = data.get('transfer_type', 'permanent')
        
        # Free agents cannot have from_club
        if transfer_type == 'free_agent' and data.get('from_club_id'):
            raise serializers.ValidationError("Free agents cannot have a from_club")
        
        # Loans and permanent transfers require from_club
        if transfer_type in ['loan', 'permanent'] and not data.get('from_club_id'):
            raise serializers.ValidationError(
                f"{transfer_type} transfers require a from_club_id"
            )
        
        # Loans require loan_end_date
        if transfer_type == 'loan' and not data.get('loan_end_date'):
            raise serializers.ValidationError("Loans must have a loan_end_date")
        
        # Validate dates
        transfer_date = data.get('transfer_date')
        loan_end_date = data.get('loan_end_date')
        
        if loan_end_date and loan_end_date <= transfer_date:
            raise serializers.ValidationError("Loan end date must be after transfer date")
        
        return data


class TransferApproveSerializer(serializers.Serializer):
    """Serializer for approving transfers."""
    pass


class TransferRejectSerializer(serializers.Serializer):
    """Serializer for rejecting transfers."""

    reason = serializers.CharField(max_length=500, required=False, allow_blank=True)


class TransferCancelSerializer(serializers.Serializer):
    """Serializer for cancelling transfers."""

    reason = serializers.CharField(max_length=500, required=False, allow_blank=True)


class LoanExtendSerializer(serializers.Serializer):
    """Serializer for extending loan duration."""

    new_end_date = serializers.DateField()

    def validate_new_end_date(self, value):
        """Validate new end date."""
        if value <= date.today():
            raise serializers.ValidationError("New end date must be in the future")
        return value


class LoanReturnSerializer(serializers.Serializer):
    """Serializer for returning a loan."""
    pass


class LoanMakePermanentSerializer(serializers.Serializer):
    """Serializer for converting loan to permanent."""

    fee = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        required=False,
        allow_null=True
    )


class TransferListSerializer(serializers.ModelSerializer):
    """Simplified transfer info for list views."""

    player_name = serializers.CharField(
        source='player.full_name',
        read_only=True
    )
    from_club_name = serializers.CharField(
        source='from_club.name',
        read_only=True,
        allow_null=True
    )
    to_club_name = serializers.CharField(
        source='to_club.name',
        read_only=True
    )
    transfer_type_display = serializers.CharField(
        source='get_transfer_type_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )

    class Meta:
        model = Transfer
        fields = [
            'id', 'player_name', 'from_club_name', 'to_club_name',
            'transfer_type', 'transfer_type_display',
            'transfer_date', 'status', 'status_display',
            'loan_end_date', 'fee'
        ]
        read_only_fields = fields
