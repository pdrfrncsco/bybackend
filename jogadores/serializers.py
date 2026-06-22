from django.db import IntegrityError, transaction
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Player, PlayerHistory

class PlayerHistorySerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=False)
    player = serializers.PrimaryKeyRelatedField(queryset=Player.objects.all(), required=False)
    player_name = serializers.CharField(source="player.name", read_only=True)
    club_name = serializers.CharField(source='club.name', read_only=True)

    class Meta:
        model = PlayerHistory
        fields = ['id', 'player', 'player_name', 'season', 'club', 'club_name', 'matches', 'goals', 'assists', 'minutes', 'yellow_cards', 'red_cards']

class PlayerStatsSerializer(serializers.Serializer):
    matches = serializers.IntegerField()
    goals = serializers.IntegerField()
    assists = serializers.IntegerField()
    minutes = serializers.IntegerField()
    yellowCards = serializers.IntegerField()
    redCards = serializers.IntegerField()

class PlayerSerializer(serializers.ModelSerializer):
    position = serializers.CharField(required=False)
    club_name = serializers.CharField(source='club.name', read_only=True)
    avatar_url = serializers.ImageField(source='avatar', read_only=True)
    history = PlayerHistorySerializer(many=True, required=False)
    stats = serializers.SerializerMethodField()
    foot = serializers.CharField(required=False)

    class Meta:
        model = Player
        fields = [
            'id', 'name', 'nickname', 'shirt_name', 'position', 'number', 'age', 
            'nationality', 'avatar', 'avatar_url', 'club', 'club_name', 'clube_profile',
            'is_captain', 'is_starter', 'created_at',
            'date_of_birth', 'status', 'height', 'weight', 'foot', 'joined_date',
            'history', 'stats'
        ]
        read_only_fields = ['id', 'created_at', 'tenant']

    @extend_schema_field(PlayerStatsSerializer)
    def get_stats(self, obj):
        # Safer approach using the model directly to avoid M2M conflict
        latest = PlayerHistory.objects.filter(player=obj).order_by('-season').first()
        
        if latest:
            return {
                "matches": latest.matches,
                "goals": latest.goals,
                "assists": latest.assists,
                "minutes": latest.minutes,
                "yellowCards": latest.yellow_cards,
                "redCards": latest.red_cards,
            }
            
        return {
            "matches": 0,
            "goals": 0,
            "assists": 0,
            "minutes": 0,
            "yellowCards": 0,
            "redCards": 0,
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if data.get("foot") == "Ambidestro":
            data["foot"] = "Ambos"
        return data

    def validate(self, attrs):
        instance = getattr(self, "instance", None)
        request = self.context.get("request")
        tenant = getattr(getattr(request, "user", None), "tenant", None)

        number = attrs.get("number", getattr(instance, "number", None))
        if number is not None and (number < 0 or number > 99):
            raise serializers.ValidationError({"number": "O número deve ser entre 0 e 99."})

        club_for_number = attrs.get("club", getattr(instance, "club", None))
        if (
            number is not None
            and club_for_number is not None
        ):
            qs = Player.objects.filter(club=club_for_number, number=number)
            if instance is not None:
                qs = qs.exclude(pk=instance.pk)
            if tenant is not None:
                qs = qs.filter(tenant=tenant)
            if qs.exists():
                raise serializers.ValidationError(
                    {"number": "Já existe um jogador com este número neste clube."}
                )

        height = attrs.get("height", getattr(instance, "height", None))
        if height is not None and (height < 100 or height > 250):
            raise serializers.ValidationError({"height": "Altura inválida."})

        weight = attrs.get("weight", getattr(instance, "weight", None))
        if weight is not None and (weight < 40 or weight > 150):
            raise serializers.ValidationError({"weight": "Peso inválido."})

        age = attrs.get("age", getattr(instance, "age", None))
        if age is not None and (age < 12 or age > 50):
            raise serializers.ValidationError({"age": "Idade inválida."})

        if instance is None and not attrs.get("club"):
            raise serializers.ValidationError({"club": "O clube é obrigatório."})

        club = attrs.get("club")
        if club is not None and tenant is not None and getattr(club, "tenant_id", None) != tenant.id:
            raise serializers.ValidationError({"club": "Clube inválido."})

        history = attrs.get("history")
        if history is not None and tenant is not None:
            for row in history:
                row_club = row.get("club")
                if row_club is not None and getattr(row_club, "tenant_id", None) != tenant.id:
                    raise serializers.ValidationError({"history": "Clube inválido no histórico."})

        position = attrs.get("position", getattr(instance, "position", None))
        if position is not None:
            normalized = position.strip().lower()

            if normalized in {"médio", "medio", "meio campo", "meio-campo"}:
                attrs["position"] = "Meio-campo"

            if normalized in {"defesa", "defesa central", "defesa-central"}:
                attrs["position"] = "Defesa-central"

            if normalized in {"extremo direito", "extremo-direito"}:
                attrs["position"] = "Extremo-direito"

            if normalized in {"extremo esquerdo", "extremo-esquerdo"}:
                attrs["position"] = "Extremo-esquerdo"

            if normalized in {"lateral direito", "lateral-direito"}:
                attrs["position"] = "Lateral-direito"

            if normalized in {"lateral esquerdo", "lateral-esquerdo"}:
                attrs["position"] = "Lateral-esquerdo"

            allowed_positions = {choice[0] for choice in Player._meta.get_field("position").choices}

            final_position = attrs.get("position", position)
            if final_position not in allowed_positions:
                raise serializers.ValidationError({"position": "Posição inválida."})

        foot = attrs.get("foot")
        if foot is not None:
            normalized_foot = foot.strip().lower()
            if normalized_foot in {"ambos", "ambidestro"}:
                attrs["foot"] = "Ambidestro"
            allowed_feet = {"Direito", "Esquerdo", "Ambidestro"}
            if attrs.get("foot") not in allowed_feet:
                raise serializers.ValidationError({"foot": "Pé preferencial inválido."})

        return attrs

    def create(self, validated_data):
        history_data = validated_data.pop("history", [])
        validated_data.pop("stats", None)
        try:
            with transaction.atomic():
                player = super().create(validated_data)
                if history_data:
                    PlayerHistory.objects.bulk_create(
                        [PlayerHistory(player=player, **row) for row in history_data]
                    )
                return player
        except IntegrityError:
            raise serializers.ValidationError(
                {"number": "Já existe um jogador com este número neste clube."}
            )

    def update(self, instance, validated_data):
        history_data = validated_data.pop("history", None)
        validated_data.pop("stats", None)
        try:
            with transaction.atomic():
                player = super().update(instance, validated_data)
                if history_data is not None:
                    player.history.all().delete()
                    if history_data:
                        PlayerHistory.objects.bulk_create(
                            [PlayerHistory(player=player, **row) for row in history_data]
                        )
                return player
        except IntegrityError:
            raise serializers.ValidationError(
                {"number": "Já existe um jogador com este número neste clube."}
            )
