from django.contrib import admin
from .models import SubscriptionPlan, Subscription


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "target_type", "plan_type", "price_amount", "billing_period", "is_active"]
    list_filter = ["target_type", "plan_type", "billing_period", "is_active"]
    search_fields = ["code", "name"]


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "subscriber_type",
        "tenant",
        "fan",
        "organization",
        "plan",
        "status",
        "payment_method",
        "amount",
        "billing_period",
    ]
    list_filter = ["subscriber_type", "status", "payment_method", "billing_period"]
    search_fields = ["id", "external_payment_id"]
