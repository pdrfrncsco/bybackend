from django.contrib import admin
from .models import Tournament, TournamentGroup


class TournamentGroupInline(admin.TabularInline):
    model = TournamentGroup
    extra = 0


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "season",
        "type",
        "status",
        "is_public",
        "tenant",
        "start_date",
        "end_date",
        "max_teams",
        "clubs_count",
        "progress",
        "champion_club",
        "runner_up_club",
    )
    list_filter = (
        "status",
        "type",
        "is_public",
        "tenant",
        "season",
        "start_date",
        "end_date",
    )
    search_fields = (
        "name",
        "season",
        "champion_club__name",
        "runner_up_club__name",
    )
    list_select_related = ("tenant", "champion_club", "runner_up_club")
    filter_horizontal = ("clubs",)
    inlines = [TournamentGroupInline]
    ordering = ("-start_date",)

    def clubs_count(self, obj):
        return obj.clubs.count()


@admin.register(TournamentGroup)
class TournamentGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "tournament", "tenant")
    list_filter = ("tenant", "tournament")
    search_fields = ("name", "tournament__name")
    raw_id_fields = ("tournament", "clubs")
