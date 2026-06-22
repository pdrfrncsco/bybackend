from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'name', 'role', 'tenant', 'is_staff')
    list_filter = ('role', 'tenant', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'name')
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('name', 'role', 'tenant', 'avatar')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Custom Fields', {'fields': ('name', 'role', 'tenant', 'avatar')}),
    )
