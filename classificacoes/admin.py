from django.contrib import admin
from .models import Standing

@admin.register(Standing)
class StandingAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'tournament', 'group', 'club', 'played', 'wins', 'draws', 'losses', 'goals_for', 'goals_against', 'points')
    list_filter = ('tenant', 'tournament', 'group', 'club')
    search_fields = ('tenant__name', 'tournament__name', 'group__name', 'club__name')
