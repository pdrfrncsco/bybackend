from django.contrib import admin
from .models import TenantSettings


@admin.register(TenantSettings)
class TenantSettingsAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'email_alerts', 'match_updates', 'marketing', 'financial_reports')
