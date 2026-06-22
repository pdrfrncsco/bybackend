from django.contrib import admin
from .models import Match


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'tournament', 'round', 'home_team', 'away_team', 'venue','status')
    list_filter = ('tournament', 'round', 'venue', 'status')
    search_fields = ('id', 'tournament__name', 'venue__name')