"""
BOLAYETU — Assinaturas Service Layer
Skills: BOLAYETU_ARCHITECTURE, BOLAYETU_BACKEND_SKILL, BOLAYETU_MULTITENANT_SKILL
"""

import uuid
import requests
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404

from common.base import BaseService
from .models import Subscription, SubscriptionPlan
from .selectors import SubscriptionSelector


class SubscriptionService(BaseService):
    """
    Service layer for mutating Subscriptions and processing payment gateways.
    """

    @BaseService.atomic
    def create_subscription(self, *, subscriber_type: str, data: dict) -> Subscription:
        """
        Creates a new subscription (tenant or fan-scoped).
        """
        subscription = Subscription(subscriber_type=subscriber_type)
        
        for field, value in data.items():
            if hasattr(subscription, field) and field not in ['id', 'subscriber_type', 'created_at', 'updated_at']:
                setattr(subscription, field, value)
                
        if subscriber_type == 'tenant':
            self._assert_tenant()
            subscription.tenant = self.tenant
        elif subscriber_type == 'fan':
            self._assert_user()
            subscription.fan = self.user
            
        subscription.full_clean()
        subscription.save()
        return subscription

    @BaseService.atomic
    def initiate_mcx_payment(self, *, plan_id: str, phone_number: str) -> dict:
        """
        Initiates a payment with the MCX Gateway.
        Creates a pending subscription and returns redirection payload.
        """
        self._assert_user()
        self._assert_tenant()
        
        plan = get_object_or_404(SubscriptionPlan, id=plan_id)
        amount = plan.price_amount
        gateway_url = getattr(settings, 'MCX_API_URL', None)
        
        if not gateway_url:
            raise ValidationError('Gateway MCX não configurado.')

        if gateway_url == 'MOCK':
            data = {
                'transaction_id': str(uuid.uuid4()),
                'status': 'success',
                'redirect_url': None,
            }
        else:
            payload = {
                'amount': str(amount),
                'phone_number': phone_number,
                'description': f'Subscrição plano {plan.name}',
            }
            try:
                response = requests.post(gateway_url, json=payload, timeout=10)
                response.raise_for_status()
                data = response.json()
            except Exception:
                raise ValidationError('Erro ao contactar o gateway MCX.')

        external_payment_id = data.get('transaction_id') or data.get('id')
        redirect_url = data.get('redirect_url') or data.get('checkout_url')

        subscription = Subscription.objects.create(
            subscriber_type='tenant',
            tenant=self.tenant,
            plan=plan,
            amount=amount,
            status='pending',
            payment_method='gateway',
            billing_period=plan.billing_period,
            external_payment_id=external_payment_id,
        )

        return {
            'subscription': subscription,
            'external_payment_id': external_payment_id,
            'redirect_url': redirect_url
        }

    @BaseService.atomic
    def initiate_unitel_payment(self, *, plan_id: str, phone_number: str) -> dict:
        """
        Initiates a payment with the Unitel Money Gateway.
        Creates a pending subscription and returns redirection payload.
        """
        self._assert_user()
        self._assert_tenant()
        
        plan = get_object_or_404(SubscriptionPlan, id=plan_id)
        amount = plan.price_amount
        gateway_url = getattr(settings, 'UNITEL_API_URL', None)
        
        if not gateway_url:
            raise ValidationError('Gateway Unitel não configurado.')

        if gateway_url == 'MOCK':
            data = {
                'transaction_id': str(uuid.uuid4()),
                'status': 'success',
                'redirect_url': None,
            }
        else:
            payload = {
                'amount': str(amount),
                'phone_number': phone_number,
                'description': f'Subscrição plano {plan.name}',
            }
            try:
                response = requests.post(gateway_url, json=payload, timeout=10)
                response.raise_for_status()
                data = response.json()
            except Exception:
                raise ValidationError('Erro ao contactar o gateway Unitel.')

        external_payment_id = data.get('transaction_id') or data.get('id')
        redirect_url = data.get('redirect_url') or data.get('checkout_url')

        subscription = Subscription.objects.create(
            subscriber_type='tenant',
            tenant=self.tenant,
            plan=plan,
            amount=amount,
            status='pending',
            payment_method='gateway',
            billing_period=plan.billing_period,
            external_payment_id=external_payment_id,
        )

        return {
            'subscription': subscription,
            'external_payment_id': external_payment_id,
            'redirect_url': redirect_url
        }

    @BaseService.atomic
    def process_gateway_webhook(self, *, external_payment_id: str, status_value: str) -> Subscription:
        """
        Processes webhooks from MCX or Unitel to update a subscription state.
        Handles transition dates, end period calculation, and cancelation of overlapping plans.
        """
        subscription = get_object_or_404(Subscription, external_payment_id=external_payment_id)
        status_value = status_value.lower()

        if status_value in ['success', 'paid', 'completed']:
            today = timezone.now().date()
            delta = SubscriptionSelector.get_billing_period_delta(subscription)
            
            if subscription.subscriber_type == 'tenant' and subscription.tenant_id:
                # Resolve overlapping active plans
                current = (
                    Subscription.objects.filter(
                        subscriber_type='tenant',
                        tenant_id=subscription.tenant_id,
                        status='active',
                        start_date__lte=today,
                    )
                    .filter(
                        Q(end_date__isnull=True) | Q(end_date__gte=today)
                    )
                    .exclude(id=subscription.id)
                    .order_by('-start_date')
                    .first()
                )

                if current and current.end_date is None:
                    # Cancel overlapping infinite subscriptions
                    subscription.status = 'canceled'
                    subscription.save()
                    return subscription

                base_end = current.end_date if current and current.end_date else today
                end_date = base_end + delta
                
                if current:
                    current.status = 'canceled'
                    current.end_date = today - timedelta(days=1)
                    current.save()
            else:
                end_date = today + delta

            subscription.start_date = today
            subscription.end_date = end_date
            subscription.status = 'active'
            
        elif status_value in ['failed', 'canceled', 'cancelled']:
            subscription.status = 'canceled'
            
        subscription.save()
        return subscription
