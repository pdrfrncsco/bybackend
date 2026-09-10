"""
BOLAYETU — Django Management Command: seed_mock_ecosystem

Executa a geração completa de dados mock através de manage.py:
    python manage.py seed_mock_ecosystem
    python manage.py seed_mock_ecosystem --user-email="admin@bolayetu.com"
    python manage.py seed_mock_ecosystem --clean
"""

from django.core.management.base import BaseCommand
from scripts.seed_mock_ecosystem import EcosystemSeeder


class Command(BaseCommand):
    help = "Gera um ecossistema completo de dados mock (Organizações, Clubes, Jogadores e Competições)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--user-email",
            type=str,
            default=None,
            help="Email do utilizador a associar como Gestor do Clube e Admin da Organização.",
        )
        parser.add_argument(
            "--clubs-per-org",
            type=int,
            default=6,
            help="Número de clubes a criar por organização (default: 6).",
        )
        parser.add_argument(
            "--players-per-club",
            type=int,
            default=22,
            help="Número de jogadores no plantel de cada clube (default: 22).",
        )
        parser.add_argument(
            "--matches-per-comp",
            type=int,
            default=4,
            help="Número de jogos a simular por competição (default: 4).",
        )
        parser.add_argument(
            "--clean",
            action="store_true",
            help="Limpar dados mocks anteriores antes de criar novos.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simular sem persistir no banco de dados.",
        )

    def handle(self, *args, **options):
        seeder = EcosystemSeeder(
            user_email=options.get("user_email"),
            clubs_per_org=options.get("clubs_per_org", 6),
            players_per_club=options.get("players_per_club", 22),
            matches_per_comp=options.get("matches_per_comp", 4),
            dry_run=options.get("dry_run", False),
        )

        clean = options.get("clean", False)
        seeder.run(clean=clean)
        self.stdout.write(self.style.SUCCESS("Geração de dados mock concluída com sucesso!"))
