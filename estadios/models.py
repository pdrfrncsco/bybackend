from django.db import models
from core.models import BaseModel, Tenant

class Stadium(BaseModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='stadiums')
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    capacity = models.IntegerField(null=True, blank=True)
    image = models.ImageField(upload_to='stadiums/', null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.location})"
