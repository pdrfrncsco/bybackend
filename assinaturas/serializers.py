from rest_framework import serializers
from django.db.models import Q
from django.utils import timezone
from .models import SubscriptionPlan, Subscription


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = [
            "id",
            "code",
            "name",
            "description",
            "target_type",
            "plan_type",
            "price_amount",
            "currency",
            "billing_period",
            "is_active",
            "max_active_tournaments",
            "max_clubs",
            "max_players",
            "max_news_articles",
            "max_followers",
            "organizer_commission_percent",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)
    plan_id = serializers.PrimaryKeyRelatedField(
        queryset=SubscriptionPlan.objects.all(),
        source="plan",
        write_only=True,
    )

    class Meta:
        model = Subscription
        fields = [
            "id",
            "subscriber_type",
            "tenant",
            "fan",
            "organization",
            "plan",
            "plan_id",
            "start_date",
            "end_date",
            "status",
            "payment_method",
            "amount",
            "billing_period",
            "external_payment_id",
            "organizer_share",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "organizer_share",
        ]

    def validate(self, attrs):
        attrs = super().validate(attrs)
        request = self.context.get("request")

        plan = attrs.get("plan")
        subscriber_type = attrs.get("subscriber_type")
        payment_method = attrs.get("payment_method")
        status_value = attrs.get("status")

        if plan and payment_method == "none" and status_value == "active":
            if plan.price_amount and plan.price_amount > 0:
                raise serializers.ValidationError(
                    {"payment_method": "Método de pagamento inválido para planos pagos."}
                )

        if (
            request
            and subscriber_type == "tenant"
            and plan is not None
            and getattr(request.user, "tenant", None) is not None
        ):
            tenant = request.user.tenant
            today = timezone.now().date()
            current = (
                Subscription.objects.filter(
                    subscriber_type="tenant",
                    tenant=tenant,
                    status="active",
                    start_date__lte=today,
                )
                .filter(Q(end_date__isnull=True) | Q(end_date__gte=today))
                .order_by("-start_date")
                .first()
            )
            if current and current.plan_id and current.plan.price_amount is not None:
                if plan.price_amount is not None and plan.price_amount < current.plan.price_amount:
                    raise serializers.ValidationError(
                        {"plan_id": "Não é possível fazer downgrade enquanto existe uma subscrição ativa."}
                    )

        return attrs

