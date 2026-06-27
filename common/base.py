"""
BOLAYETU — Base Classes for Services and Selectors
Following Clean Architecture and DDD principles
"""

from django.db import transaction


class BaseService:
    """
    Base class for all service layer classes.
    Services handle business logic and mutations.
    """
    
    def __init__(self, user=None, tenant=None):
        self.user = user
        self.tenant = tenant
    
    def _assert_user(self):
        """Assert that a user is provided"""
        if not self.user:
            raise ValueError("User is required for this operation")
    
    def _assert_tenant(self):
        """Assert that a tenant is provided"""
        if not self.tenant:
            raise ValueError("Tenant is required for this operation")
    
    @staticmethod
    def atomic(func):
        """Decorator to wrap function in atomic transaction"""
        def wrapper(*args, **kwargs):
            with transaction.atomic():
                return func(*args, **kwargs)
        return wrapper


class BaseSelector:
    """
    Base class for all selector layer classes.
    Selectors handle data retrieval and queries.
    """
    
    def __init__(self, user=None, tenant=None):
        self.user = user
        self.tenant = tenant
    
    def _assert_user(self):
        """Assert that a user is provided"""
        if not self.user:
            raise ValueError("User is required for this operation")
    
    def _assert_tenant(self):
        """Assert that a tenant is provided"""
        if not self.tenant:
            raise ValueError("Tenant is required for this operation")
