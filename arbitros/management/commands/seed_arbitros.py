from datetime import date, timedelta

from django.core.management.base import BaseCommand, CommandError

from core.models import Tenant
from arbitros.models import Referee, RefereeAvailability


class Command(BaseCommand):
    help = 'Gera árbitros de exemplo para um tenant'

    def add_arguments(self, parser):
        parser.add_argument('--tenant-slug', type=str, required=True)
        parser.add_argument('--count', type=int, default=16)

    def handle(self, *args, **options):
        tenant_slug = options['tenant_slug']
        count = options.get('count') or 16

        try:
            tenant = Tenant.objects.get(slug=tenant_slug)
        except Tenant.DoesNotExist:
            raise CommandError(f'Tenant com slug "{tenant_slug}" não encontrado.')

        categories = ['international', 'national', 'regional', 'local']

        total_created = 0
        total_updated = 0
        total_avail = 0

        base_date = date(2025, 1, 1)

        for i in range(1, count + 1):
            category = categories[(i - 1) % len(categories)]
            name = f'Árbitro {i} {tenant.slug.title()}'
            bi = f'{tenant.slug.upper()}-{i:04d}'
            phone = f'+244900{i:04d}'
            email = f'arbitro{i}@{tenant.slug}.test'

            defaults = {
                'name': name,
                'category': category,
                'phone': phone,
                'email': email,
                'is_active': True,
            }

            referee, created = Referee.objects.update_or_create(
                tenant=tenant,
                bi=bi,
                defaults=defaults,
            )

            if created:
                total_created += 1
            else:
                total_updated += 1

            for offset in range(3):
                availability_date = base_date + timedelta(days=(i - 1) * 3 + offset)
                is_available = offset != 1
                notes = '' if is_available else 'Indisponível por motivo pessoal.'

                RefereeAvailability.objects.update_or_create(
                    tenant=tenant,
                    referee=referee,
                    date=availability_date,
                    defaults={
                        'is_available': is_available,
                        'notes': notes,
                    },
                )
                total_avail += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Seed de árbitros executado para tenant {tenant.slug}: '
                f'{count} perfis, {total_created} criados, {total_updated} atualizados, '
                f'{total_avail} disponibilidades'
            )
        )

