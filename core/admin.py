from django.contrib import admin
from .models import Tenant


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'type', 'is_public', 'is_active', 'verified']
    list_filter = ['type', 'is_public', 'is_active', 'verified']
    search_fields = ['name', 'slug', 'email']
    prepopulated_fields = {'slug': ('name',)}
