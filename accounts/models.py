"""
BOLAYETU — Accounts Models
Custom User Model and Profile Models
"""

import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from core.models import Tenant


class User(AbstractUser):
    """
    Custom User model.
    Handles identity, authentication, and authorization.
    Business profiles are kept separate.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    avatar = models.ImageField(upload_to='users/avatars/', null=True, blank=True)
    
    # Multi-tenant relationship
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    
    # Subscriptions (fan following organizations)
    subscriptions = models.ManyToManyField(
        Tenant,
        blank=True,
        related_name='subscribers'
    )
    
    # Profile type (to be extended)
    profile_type = models.CharField(
        max_length=20,
        choices=[
            ('admin', 'Admin'),
            ('organization', 'Organização'),
            ('club', 'Clube'),
            ('player', 'Jogador'),
            ('fan', 'Adepto'),
        ],
        default='fan'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_at = models.DateTimeField(null=True, blank=True)
    
    # Settings
    language = models.CharField(max_length=5, default='pt')
    timezone = models.CharField(max_length=50, default='Africa/Luanda')
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.email} ({self.get_profile_type_display()})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username
