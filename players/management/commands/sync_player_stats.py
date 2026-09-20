"""
Management command to recalculate and synchronize statistics for all players.

Updates:
- PlayerRegistration stats (matches_played, goals, assists, yellow/red cards)
- PlayerCareer rows (club, season, appearances, goals, assists)
- PlayerSeasonStatistics rows
- Global Player total aggregates (total_matches, total_goals, total_assists)
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from players.models import Player, PlayerRegistration
from players.services.stats_sync_service import StatsSyncService
from players.services.player_career_service import PlayerCareerService
from players.services.player_statistics_service import PlayerStatisticsService


class Command(BaseCommand):
    help = "Recalculate and synchronize stats, career timelines and season statistics for all players."

    def add_arguments(self, parser):
        parser.add_argument(
            "--player",
            type=str,
            help="Specific player slug or UUID to sync.",
        )

    def handle(self, *args, **options):
        player_arg = options.get("player")
        if player_arg:
            players = Player.objects.filter(slug=player_arg) or Player.objects.filter(id=player_arg)
        else:
            players = Player.objects.all()

        total = players.count()
        self.stdout.write(f"Starting stats synchronization for {total} players...")

        synced_count = 0
        with transaction.atomic():
            for p in players:
                # 1. Recalculate registrations
                registrations = PlayerRegistration.objects.filter(player=p)
                for reg in registrations:
                    StatsSyncService._recalculate_registration_stats(reg)

                # 2. Rebuild season statistics
                PlayerStatisticsService.rebuild_for_player(p)

                # 3. Rebuild career timeline
                PlayerCareerService.rebuild_career_for_player(p)

                # 4. Update denormalized player totals
                StatsSyncService._update_player_totals(p)

                synced_count += 1
                if synced_count % 25 == 0 or synced_count == total:
                    self.stdout.write(f"  Processed {synced_count}/{total} players...")

        self.stdout.write(self.style.SUCCESS(f"Successfully synchronized {synced_count} players!"))
