"""
BOLAYETU — PlayerCategory Serializers

Serializers for player category management by federations and clubs.
"""

from rest_framework import serializers

from players.models.category import PlayerCategory


class PlayerCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for displaying player categories.
    """

    tenant_name = serializers.CharField(source="tenant.name", read_only=True)
    club_name = serializers.CharField(source="club.name", read_only=True, default=None)
    gender_label = serializers.CharField(source="get_gender_display", read_only=True)
    scope_label = serializers.CharField(source="get_scope_display", read_only=True)
    players_count = serializers.SerializerMethodField()

    class Meta:
        model = PlayerCategory
        fields = [
            "id",
            "tenant",
            "tenant_name",
            "club",
            "club_name",
            "scope",
            "scope_label",
            "name",
            "slug",
            "min_age",
            "max_age",
            "gender",
            "gender_label",
            "is_custom",
            "is_active",
            "display_order",
            "players_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "tenant",
            "tenant_name",
            "club",
            "club_name",
            "scope",
            "scope_label",
            "slug",
            "is_custom",
            "players_count",
            "created_at",
            "updated_at",
        ]

    def get_players_count(self, obj: PlayerCategory) -> int:
        """Returns the number of active registered players in this category."""
        return obj.registrations.filter(status__in=["registered", "loaned"]).count()


class PlayerCategoryCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new player category.
    """

    class Meta:
        model = PlayerCategory
        fields = [
            "name",
            "min_age",
            "max_age",
            "gender",
            "is_active",
            "display_order",
        ]

    def validate(self, attrs):
        min_age = attrs.get("min_age")
        max_age = attrs.get("max_age")
        if min_age is not None and max_age is not None and min_age >= max_age:
            raise serializers.ValidationError(
                {"max_age": "A idade máxima deve ser superior à idade mínima."}
            )
        return attrs


class PlayerCategoryUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating an existing player category.
    """

    class Meta:
        model = PlayerCategory
        fields = [
            "name",
            "min_age",
            "max_age",
            "gender",
            "is_active",
            "display_order",
        ]

    def validate(self, attrs):
        instance = getattr(self, "instance", None)
        min_age = attrs.get("min_age", getattr(instance, "min_age", None))
        max_age = attrs.get("max_age", getattr(instance, "max_age", None))
        if min_age is not None and max_age is not None and min_age >= max_age:
            raise serializers.ValidationError(
                {"max_age": "A idade máxima deve ser superior à idade mínima."}
            )
        return attrs
