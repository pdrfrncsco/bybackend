from django.contrib import admin
from .models import Tenant


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'slug',
        'type',
        'country',
        'is_public',
        'verified',
        'created_at',
    )
    list_filter = ('type', 'country', 'is_public', 'verified')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
