from django.contrib import admin
from .models import Club, ClubHistory, Staff


class ClubHistoryInline(admin.TabularInline):
    model = ClubHistory
    extra = 1


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "acronym",
        "tenant",
        "founded_year",
        "location",
        "stadium_name",
        "stadium_capacity",
        "active_players",
    )
    list_filter = ("tenant", "founded_year", "location")
    search_fields = (
        "name",
        "acronym",
        "short_name",
        "location",
        "president",
        "email",
        "phone",
    )
    inlines = [ClubHistoryInline]


@admin.register(ClubHistory)
class ClubHistoryAdmin(admin.ModelAdmin):
    list_display = ("club", "season", "tournament_name", "placement", "is_trophy")
    list_filter = ("season", "is_trophy", "club__tenant")
    search_fields = ("club__name", "tournament_name", "season")


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ("name", "role", "club", "tenant", "nationality")
    list_filter = ("tenant", "club", "role", "nationality")
    search_fields = ("name", "role", "club__name", "email", "phone")
