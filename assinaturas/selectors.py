"""
BOLAYETU — Assinaturas Selector Layer
Skills: BOLAYETU_ARCHITECTURE, BOLAYETU_BACKEND_SKILL, BOLAYETU_MULTITENANT_SKILL
"""

from datetime import timedelta
from django.db.models import QuerySet, Q
from django.utils import timezone
from common.base import BaseSelector
from .models import Subscription


class SubscriptionSelector(BaseSelector):
    """
    Selector layer for retrieving Subscription records.
    """

    def list_subscriptions(self) -> QuerySet:
        """
        List subscriptions visible to the current user (taking roles and tenants into account).
        """
        self._assert_user()
        
        if self.user.is_superuser or getattr(self.user, 'role', '') == 'superadmin':
            return Subscription.objects.all()
            
        qs = Subscription.objects.none()
        
        # User is organization member -> can view organization plan and fan followers of organization
        if self.tenant:
            qs = qs | Subscription.objects.filter(subscriber_type='tenant', tenant=self.tenant)
            qs = qs | Subscription.objects.filter(subscriber_type='fan', organization=self.tenant)
            
        # User is fan -> can view their own sub details
        qs = qs | Subscription.objects.filter(subscriber_type='fan', fan=self.user)
        return qs

    def get_active_tenant_subscription(self, tenant) -> Subscription | None:
        """
        Resolve the currently active or pending subscription for the given tenant.
        """
        qs = Subscription.objects.filter(subscriber_type='tenant', tenant=tenant)
        today = timezone.now().date()

        # 1. Look for active subscription currently in range
        instance = (
            qs.filter(status='active', start_date__lte=today)
            .filter(Q(end_date__isnull=True) | Q(end_date__gte=today))
            .order_by('-start_date')
            .first()
        )

        # 2. Fallback to recently expired active subscription
        if not instance:
            instance = (
                qs.filter(status__in=['active', 'expired'], start_date__lte=today)
                .filter(end_date__isnull=False, end_date__lt=today)
                .order_by('-end_date', '-start_date')
                .first()
            )

        # 3. Fallback to pending subscription starting today
        if not instance:
            instance = (
                qs.filter(status='pending', start_date__lte=today)
                .order_by('-start_date')
                .first()
            )

        # 4. Ultimate fallback: absolute most recent subscription
        if not instance:
            instance = qs.order_by('-start_date').first()

        return instance

    def list_fan_subscriptions(self) -> QuerySet:
        """
        Retrieve all fan subscriptions for the current user.
        """
        self._assert_user()
        return Subscription.objects.filter(subscriber_type='fan', fan=self.user).order_by('-start_date')

    @staticmethod
    def get_billing_period_delta(subscription) -> timedelta:
        """
        Helper method to resolve the duration of a billing period.
        """
        period = subscription.billing_period or getattr(subscription.plan, 'billing_period', None) or 'monthly'
        if period == 'yearly':
            return timedelta(days=365)
        return timedelta(days=30)
