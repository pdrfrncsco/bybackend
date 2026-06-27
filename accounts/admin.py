from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['email', 'username', 'full_name', 'profile_type', 'tenant', 'is_active']
    list_filter = ['profile_type', 'is_active', 'is_staff', 'tenant']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Profile', {'fields': ('phone', 'avatar', 'profile_type', 'tenant', 'subscriptions')}),
        ('Settings', {'fields': ('language', 'timezone')}),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Profile', {'fields': ('email', 'profile_type')}),
    )
