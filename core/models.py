"""
BOLAYETU — Core Models
Tenant (Organization) Model for Multi-Tenant Architecture
"""

import uuid
from django.db import models
from django.utils.text import slugify


class TimeStampedModel(models.Model):
    """Abstract base model with created/updated timestamps"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    """Abstract base model with UUID primary key"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class Tenant(UUIDModel, TimeStampedModel):
    """
    Tenant model representing an Organization.
    Each tenant is isolated and has its own data.
    """
    TYPE_CHOICES = [
        ('federation', 'Federação'),
        ('association', 'Associação'),
        ('club', 'Clube'),
        ('academy', 'Academia'),
    ]
    
    # Core fields
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='federation')
    
    # Branding
    logo = models.ImageField(upload_to='tenants/logos/', null=True, blank=True)
    primary_color = models.CharField(max_length=7, default='#014D40')
    secondary_color = models.CharField(max_length=7, default='#94D3C1')
    
    # Contact
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    
    # Location
    country = models.CharField(max_length=100, default='Angola')
    location = models.CharField(max_length=255, null=True, blank=True)
    
    # Description
    description = models.TextField(null=True, blank=True)
    
    # Status
    is_public = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    verified = models.BooleanField(default=False)
    
    # Subdomain (for multi-tenant routing)
    subdomain = models.CharField(max_length=63, unique=True, null=True, blank=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
