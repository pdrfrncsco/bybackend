from django.contrib import admin
from .models import Player, PlayerHistory

# Register your models here.

class PlayerHistoryInline(admin.TabularInline):
    model = PlayerHistory
    extra = 1
    fields = ('season', 'club', 'matches', 'goals', 'assists')

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('name', 'club', 'last_club', 'position', 'nationality', 'status', 'age')
    list_filter = ('club', 'position', 'last_club', 'nationality', 'status', 'foot')
    search_fields = ('name', 'nickname')
    inlines = [PlayerHistoryInline]

@admin.register(PlayerHistory)
class PlayerHistoryAdmin(admin.ModelAdmin):
    list_display = ('player', 'season', 'club', 'matches', 'goals')
    search_fields = ('player__name', 'season', 'club')
    list_filter = ('season', 'club')