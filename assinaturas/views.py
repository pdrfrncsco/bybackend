"""
BOLAYETU — Assinaturas View Layer
Skills: BOLAYETU_ARCHITECTURE, BOLAYETU_BACKEND_SKILL, BOLAYETU_MULTITENANT_SKILL

Rule: ViewSets ONLY orchestrate. Delegate queries to selectors and database writes to services.
"""

from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.permissions import IsAdmin
from notifications.models import Notification
from .models import SubscriptionPlan, Subscription
from .serializers import SubscriptionPlanSerializer, SubscriptionSerializer
from .selectors import SubscriptionSelector
from .services import SubscriptionService

User = get_user_model()


class SubscriptionPlanViewSet(viewsets.ModelViewSet):
    queryset = SubscriptionPlan.objects.all()
    serializer_class = SubscriptionPlanSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [IsAdmin()]


class SubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Subscription.objects.none()
            
        tenant = getattr(self.request, 'tenant', None) or getattr(self.request.user, 'tenant', None)
        selector = SubscriptionSelector(tenant=tenant, user=self.request.user)
        return selector.list_subscriptions()

    def perform_create(self, serializer):
        tenant = getattr(self.request, 'tenant', None) or getattr(self.request.user, 'tenant', None)
        service = SubscriptionService(user=self.request.user, tenant=tenant)
        subscriber_type = serializer.validated_data.get("subscriber_type")
        service.create_subscription(subscriber_type=subscriber_type, data=serializer.validated_data)

    @action(detail=False, methods=["get"], url_path="me/tenant")
    def me_tenant_subscription(self, request):
        tenant = getattr(request.user, "tenant", None)
        if not tenant:
            return Response({"detail": "Tenant não definido."}, status=400)
        
        selector = SubscriptionSelector(tenant=tenant, user=request.user)
        instance = selector.get_active_tenant_subscription(tenant)

        if not instance:
            return Response({"detail": "Nenhuma assinatura encontrada."}, status=404)

        # Trigger notification triggers if subscription is nearing end or has expired
        today = timezone.now().date()
        end_date = instance.end_date
        link = "/dashboard/subscription"
        
        if end_date:
            days_until_end = (end_date - today).days
            recipients = list(User.objects.filter(tenant=tenant, role__in=["admin", "manager"]))
            if request.user not in recipients:
                recipients.append(request.user)

            if instance.status == "active" and 0 <= days_until_end <= 7:
                message = f"A sua subscrição ({instance.plan.name}) termina em {end_date.strftime('%d/%m/%Y')}. Renove para evitar interrupções."
                title = "Subscrição a terminar"
                for u in recipients:
                    if not Notification.objects.filter(user=u, title=title, message=message, type="warning").exists():
                        Notification.objects.create(user=u, title=title, message=message, type="warning", link=link)

            if instance.status in ["active", "expired"] and days_until_end < 0:
                message = f"A sua subscrição ({instance.plan.name}) expirou em {end_date.strftime('%d/%m/%Y')}. Renove para voltar a ter acesso completo."
                title = "Subscrição expirada"
                for u in recipients:
                    if not Notification.objects.filter(user=u, title=title, message=message, type="error").exists():
                        Notification.objects.create(user=u, title=title, message=message, type="error", link=link)
                        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="me/fan")
    def me_fan_subscriptions(self, request):
        tenant = getattr(request, 'tenant', None) or getattr(request.user, 'tenant', None)
        selector = SubscriptionSelector(tenant=tenant, user=request.user)
        qs = selector.list_fan_subscriptions()
        
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    # ─── Payment Gateway Integration Endpoints ─────────────────────

    @action(detail=False, methods=["post"], url_path="pay_mcx")
    def pay_mcx(self, request):
        tenant = getattr(request.user, "tenant", None)
        if not tenant:
            return Response({"detail": "Tenant não definido."}, status=status.HTTP_400_BAD_REQUEST)

        plan_id = request.data.get("plan_id") or request.data.get("planId")
        phone_number = request.data.get("phone_number") or request.data.get("phoneNumber")
        if not plan_id or not phone_number:
            return Response({"detail": "plan_id e phone_number são obrigatórios."}, status=status.HTTP_400_BAD_REQUEST)

        service = SubscriptionService(user=request.user, tenant=tenant)
        result = service.initiate_mcx_payment(plan_id=plan_id, phone_number=phone_number)
        
        serializer = self.get_serializer(result['subscription'])
        return Response(
            {
                "subscription": serializer.data,
                "gateway": "mcx",
                "external_payment_id": result['external_payment_id'],
                "redirect_url": result['redirect_url'],
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["post"], url_path="pay_unitel")
    def pay_unitel(self, request):
        tenant = getattr(request.user, "tenant", None)
        if not tenant:
            return Response({"detail": "Tenant não definido."}, status=status.HTTP_400_BAD_REQUEST)

        plan_id = request.data.get("plan_id") or request.data.get("planId")
        phone_number = request.data.get("phone_number") or request.data.get("phoneNumber")
        if not plan_id or not phone_number:
            return Response({"detail": "plan_id e phone_number são obrigatórios."}, status=status.HTTP_400_BAD_REQUEST)

        service = SubscriptionService(user=request.user, tenant=tenant)
        result = service.initiate_unitel_payment(plan_id=plan_id, phone_number=phone_number)
        
        serializer = self.get_serializer(result['subscription'])
        return Response(
            {
                "subscription": serializer.data,
                "gateway": "unitel",
                "external_payment_id": result['external_payment_id'],
                "redirect_url": result['redirect_url'],
            },
            status=status.HTTP_201_CREATED,
        )

    # ─── Payment Webhooks ──────────────────────────────────────────

    @action(
        detail=False,
        methods=["post"],
        url_path="mcx_webhook",
        permission_classes=[permissions.AllowAny],
        authentication_classes=[],
    )
    def mcx_webhook(self, request):
        data = request.data or {}
        external_payment_id = (
            data.get("transaction_id") or data.get("id") or data.get("reference")
        )
        if not external_payment_id:
            return Response(
                {"detail": "Identificador de transacção em falta."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        secret = getattr(settings, "MCX_WEBHOOK_SECRET", None)
        if secret:
            received = request.headers.get("X-Webhook-Secret")
            if received != secret:
                return Response(
                    {"detail": "Não autorizado."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        service = SubscriptionService()
        status_value = (data.get("status") or data.get("payment_status") or "").lower()
        subscription = service.process_gateway_webhook(
            external_payment_id=external_payment_id,
            status_value=status_value
        )

        serializer = self.get_serializer(subscription)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["post"],
        url_path="unitel_webhook",
        permission_classes=[permissions.AllowAny],
        authentication_classes=[],
    )
    def unitel_webhook(self, request):
        data = request.data or {}
        external_payment_id = (
            data.get("transaction_id") or data.get("id") or data.get("reference")
        )
        if not external_payment_id:
            return Response(
                {"detail": "Identificador de transacção em falta."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        secret = getattr(settings, "UNITEL_WEBHOOK_SECRET", None)
        if secret:
            received = request.headers.get("X-Webhook-Secret")
            if received != secret:
                return Response(
                    {"detail": "Não autorizado."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        service = SubscriptionService()
        status_value = (data.get("status") or data.get("payment_status") or "").lower()
        subscription = service.process_gateway_webhook(
            external_payment_id=external_payment_id,
            status_value=status_value
        )

        serializer = self.get_serializer(subscription)
        return Response(serializer.data)
