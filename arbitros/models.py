from django.db import models
from core.models import BaseModel, Tenant

class Referee(BaseModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='referees')
    name = models.CharField(max_length=255)
    bi = models.CharField(max_length=50, unique=True)
    category = models.CharField(
        max_length=50,
        choices=[
            ('international', 'Internacional'),
            ('national', 'Nacional'),
            ('regional', 'Regional'),
            ('local', 'Local'),
        ],
    )
    phone = models.CharField(max_length=50)
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)


class RefereeAvailability(BaseModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='referee_availabilities')
    referee = models.ForeignKey(Referee, on_delete=models.CASCADE, related_name='availabilities')
    date = models.DateField()
    is_available = models.BooleanField(default=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ('tenant', 'referee', 'date')
