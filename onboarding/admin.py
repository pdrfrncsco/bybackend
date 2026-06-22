from django.contrib import admin
from onboarding.models import OnboardingRequest

@admin.register(OnboardingRequest)
class OnboardingAdmin(admin.ModelAdmin):
    list_display = ('organization_name','status','created_at', 'updated_at')
    list_filter = ('status','created_at', 'updated_at')

