from django.contrib import admin
from .models import Referee, RefereeAvailability


class RefereeAvailabilityInline(admin.TabularInline):
    model = RefereeAvailability
    extra = 0


@admin.register(Referee)
class RefereeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "bi",
        "category",
        "tenant",
        "phone",
        "email",
        "is_active",
        "created_at",
    )
    list_filter = (
        "tenant",
        "category",
        "is_active",
        "created_at",
    )
    search_fields = (
        "name",
        "bi",
        "phone",
        "email",
    )
    inlines = [RefereeAvailabilityInline]


@admin.register(RefereeAvailability)
class RefereeAvailabilityAdmin(admin.ModelAdmin):
    list_display = (
        "referee",
        "tenant",
        "date",
        "is_available",
    )
    list_filter = (
        "tenant",
        "is_available",
        "date",
    )
    search_fields = (
        "referee__name",
        "referee__bi",
    )
