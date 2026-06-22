from django.db import models
from core.models import BaseModel, Tenant


class Advertisement(BaseModel):
    PLACEMENT_CHOICES = (
        ('banner_top', 'Banner Top'),
        ('sidebar', 'Sidebar'),
        ('news_feed', 'News Feed'),
        ('match_center', 'Match Center'),
    )

    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    )

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='advertisements', null=True, blank=True)
    title = models.CharField(max_length=255)
    client_name = models.CharField(max_length=255, blank=True)
    image_url = models.URLField(max_length=500)
    link_url = models.URLField(max_length=500)
    placement = models.CharField(max_length=50, choices=PLACEMENT_CHOICES, default='banner_top')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    impressions = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

