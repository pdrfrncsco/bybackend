from django.db import models
from core.models import BaseModel

class OnboardingRequest(BaseModel):
    ORGANIZATION_TYPES = [
        ('league', 'Liga Profissional'),
        ('association', 'Associação'),
        ('tournament', 'Torneio'),
        ('amateur', 'Amador / Corporativo'),
        ('school', 'Escola / Formação'),
        ('federation', 'Federação'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
    ]

    organization_name = models.CharField(max_length=255)
    organization_slug = models.SlugField(unique=True)
    organization_type = models.CharField(max_length=50, choices=ORGANIZATION_TYPES, default='league')
    country = models.CharField(max_length=100, default='Angola')
    primary_color = models.CharField(max_length=7, default='#22c55e')
    logo = models.ImageField(upload_to='onboarding/logos/', null=True, blank=True)
    season_name = models.CharField(max_length=255, default='2024/25')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.organization_name} ({self.status})"
