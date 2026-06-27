from django.core.management.base import BaseCommand, CommandError
from core.models import Tenant
from clubs.models import Club
from jogadores.models import Player


class Command(BaseCommand):
    help = 'Gera jogadores de Angola para um clube ou todos os clubs de um tenant'

    def add_arguments(self, parser):
        parser.add_argument('--tenant-slug', type=str, required=True)
        parser.add_argument('--club-id', type=str, required=False)
        parser.add_argument('--players-per-club', type=int, default=15)
        parser.add_argument('--list-clubs', action='store_true', help='Lista clubs do tenant e termina')

    def handle(self, *args, **options):
        tenant_slug = options['tenant_slug']
        club_id = options.get('club_id')
        players_per_club = options.get('players_per_club') or 15
        list_clubs = options.get('list_clubs') or False

        try:
            tenant = Tenant.objects.get(slug=tenant_slug)
        except Tenant.DoesNotExist:
            raise CommandError(f'Tenant com slug "{tenant_slug}" não encontrado.')

        clubs_qs = Club.objects.filter(tenant=tenant).order_by('name')

        if list_clubs:
            self.stdout.write(
                self.style.MIGRATE_HEADING(f'Clubs do tenant "{tenant.slug}":')
            )
            for club in clubs_qs:
                self.stdout.write(f'- {club.id} - {club.name} ({club.acronym or ""})')
            return

        if club_id:
            clubs_qs = clubs_qs.filter(id=club_id)
            if not clubs_qs.exists():
                raise CommandError(
                    f'Clube com id "{club_id}" não encontrado para o tenant "{tenant_slug}".'
                )

        if not clubs_qs.exists():
            self.stdout.write(
                self.style.WARNING(f'Nenhum clube encontrado para o tenant {tenant.slug}.')
            )
            return

        total_created = 0
        total_updated = 0

        position_cycle = [
            'Guarda-Redes',
            'Defesa-central',
            'Lateral-direito',
            'Lateral-esquerdo',
            'Defesa-central',
            'Médio-direito',
            'Médio-esquerdo',
            'Meio-campo',
            'Extremo-direito',
            'Extremo-esquerdo',
            'Avançado',
            'Avançado',
        ]

        for club in clubs_qs:
            acronym = club.acronym or club.name[:3].upper()
            for number in range(1, players_per_club + 1):
                position = position_cycle[(number - 1) % len(position_cycle)]

                name = f'Jogador {number} {acronym}'
                nickname = f'{acronym} {number:02d}'
                shirt_name = f'J{number:02d} {acronym}'[:15]
                age = 18 + ((number - 1) % 15)

                player, created = Player.objects.update_or_create(
                    tenant=tenant,
                    club=club,
                    number=number,
                    defaults={
                        'name': name,
                        'nickname': nickname,
                        'shirt_name': shirt_name,
                        'position': position,
                        'age': age,
                        'nationality': 'Angolana',
                        'status': 'active',
                    },
                )
                if created:
                    total_created += 1
                else:
                    total_updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Seed de jogadores de Angola executado para tenant {tenant.slug}: '
                f'{clubs_qs.count()} clubs, {total_created} jogadores criados, {total_updated} atualizados'
            )
        )
