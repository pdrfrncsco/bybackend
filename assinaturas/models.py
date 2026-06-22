from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum
from django.dispatch import receiver
from django.db.models.signals import post_save
from datetime import datetime

from core.models import BaseModel, Tenant
from usuarios.models import User
from notifications.models import Notification


class SubscriptionPlan(BaseModel):
    TARGET_CHOICES = (
        ("tenant", "Tenant"),
        ("fan", "Fan"),
    )

    PLAN_TYPE_CHOICES = (
        ("free", "Free"),
        ("freemium", "Freemium"),
        ("basic", "Basic"),
        ("pro", "Professional"),
        ("premium", "Premium"),
        ("advanced", "Advanced"),
    )

    BILLING_PERIOD_CHOICES = (
        ("monthly", "Monthly"),
        ("yearly", "Yearly"),
    )

    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")
    target_type = models.CharField(max_length=20, choices=TARGET_CHOICES)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPE_CHOICES)
    price_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default="AOA")
    billing_period = models.CharField(max_length=20, choices=BILLING_PERIOD_CHOICES, default="monthly")
    is_active = models.BooleanField(default=True)
    max_active_tournaments = models.PositiveIntegerField(null=True, blank=True)
    max_clubs = models.PositiveIntegerField(null=True, blank=True)
    max_players = models.PositiveIntegerField(null=True, blank=True)
    max_news_articles = models.PositiveIntegerField(null=True, blank=True)
    max_followers = models.PositiveIntegerField(null=True, blank=True)
    organizer_commission_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        ordering = ["target_type", "price_amount"]

    def __str__(self):
        return f"{self.name} ({self.target_type})"


class Subscription(BaseModel):
    SUBSCRIBER_TYPE_CHOICES = (
        ("tenant", "Tenant"),
        ("fan", "Fan"),
    )

    STATUS_CHOICES = (
        ("active", "Active"),
        ("canceled", "Canceled"),
        ("expired", "Expired"),
        ("pending", "Pending"),
    )

    PAYMENT_METHOD_CHOICES = (
        ("none", "None"),
        ("offline", "Offline"),
        ("gateway", "Gateway"),
    )

    subscriber_type = models.CharField(max_length=20, choices=SUBSCRIBER_TYPE_CHOICES)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="plan_subscriptions", null=True, blank=True)
    fan = models.ForeignKey(User, on_delete=models.CASCADE, related_name="plan_subscriptions", null=True, blank=True)
    organization = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="fan_plan_subscriptions", null=True, blank=True)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name="subscriptions")
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default="none")
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    billing_period = models.CharField(max_length=20, choices=SubscriptionPlan.BILLING_PERIOD_CHOICES, default="monthly")
    external_payment_id = models.CharField(max_length=100, blank=True, default="")
    organizer_share = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.subscriber_type == "tenant":
            if not self.tenant:
                raise ValidationError({"tenant": "Tenant é obrigatório para assinaturas de organização."})
            if self.fan or self.organization:
                raise ValidationError({"subscriber_type": "Assinaturas de organização não podem ter fan ou organização associados."})
        if self.subscriber_type == "fan":
            if not self.fan or not self.organization:
                raise ValidationError({"subscriber_type": "Assinaturas de adepto requerem fan e organização."})
            if self.tenant:
                raise ValidationError({"tenant": "Não associe tenant diretamente em assinaturas de adepto."})
        if self.billing_period != self.plan.billing_period:
            raise ValidationError({"billing_period": "Período de faturação deve coincidir com o plano."})
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "Data de término não pode ser anterior à data de início."})
        if self.status == "active":
            qs = Subscription.objects.filter(
                subscriber_type=self.subscriber_type,
                plan__target_type=self.plan.target_type,
                status="active",
            )
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if self.subscriber_type == "tenant" and self.tenant:
                qs = qs.filter(tenant=self.tenant)
            if self.subscriber_type == "fan" and self.fan and self.organization:
                qs = qs.filter(fan=self.fan, organization=self.organization)
            if qs.exists():
                raise ValidationError({"status": "Já existe uma assinatura ativa para este contexto."})

    def save(self, *args, **kwargs):
        if isinstance(self.start_date, datetime):
            self.start_date = self.start_date.date()
        if self.end_date and isinstance(self.end_date, datetime):
            self.end_date = self.end_date.date()
        if not self.amount:
            self.amount = self.plan.price_amount
        if not self.organizer_share and self.plan.organizer_commission_percent:
            self.organizer_share = (self.amount * self.plan.organizer_commission_percent) / 100
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        if self.status != "active":
            return False
        if self.start_date and self.start_date > timezone.now().date():
            return False
        if self.end_date and self.end_date < timezone.now().date():
            return False
        return True

    @classmethod
    def total_organizer_earnings(cls, tenant):
        return (
            cls.objects.filter(organization=tenant, status="active").aggregate(total=Sum("organizer_share")).get("total")
            or 0
        )


@receiver(post_save, sender=Subscription)
def subscription_post_save(sender, instance, created, **kwargs):
    try:
        user = None
        title = ""
        message = ""
        if instance.subscriber_type == "tenant" and instance.tenant:
            user = User.objects.filter(tenant=instance.tenant, role__in=["admin", "manager"]).first()
            title = "Plano de organização actualizado"
            if created:
                message = f"Novo plano {instance.plan.name} ativado para a organização {instance.tenant.name}."
            else:
                message = f"Assinatura da organização {instance.tenant.name} foi actualizada para o plano {instance.plan.name}."
        if instance.subscriber_type == "fan" and instance.fan and instance.organization:
            user = instance.fan
            title = "Assinatura de adepto actualizada"
            if created:
                message = f"Está agora a seguir {instance.organization.name} com o plano {instance.plan.name}."
            else:
                message = f"A sua assinatura para {instance.organization.name} foi actualizada para o plano {instance.plan.name}."
        if user and title and message:
            Notification.objects.create(
                user=user,
                title=title,
                message=message,
                type="info",
            )
    except Exception:
        if settings.DEBUG:
            raise
