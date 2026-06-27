from django.core.management.base import BaseCommand
from core.models import Tenant
from clubs.models import Club


class Command(BaseCommand):
    help = 'Gera clubs de Angola para um tenant específico'

    def add_arguments(self, parser):
        parser.add_argument('--tenant-slug', type=str, required=True)

    def handle(self, *args, **options):
        tenant_slug = options['tenant_slug']
        tenant, _ = Tenant.objects.get_or_create(slug=tenant_slug, defaults={'name': tenant_slug})

        clubs_data = [
            {
                'key': 'petro',
                'name': 'Atlético Petróleos de Luanda',
                'short_name': 'Petro Luanda',
                'acronym': 'PET',
                'founded_year': 1980,
                'location': 'Luanda',
                'stadium_name': 'Estádio 11 de Novembro',
                'primary_color': '#FFD200',
                'secondary_color': '#0000FF',
            },
            {
                'key': 'dagosto',
                'name': 'Clube Desportivo 1º de Agosto',
                'short_name': '1º de Agosto',
                'acronym': 'AGO',
                'founded_year': 1977,
                'location': 'Luanda',
                'stadium_name': 'Estádio 11 de Novembro',
                'primary_color': '#FF0000',
                'secondary_color': '#000000',
            },
            {
                'key': 'interclube',
                'name': 'Grupo Desportivo Interclube',
                'short_name': 'Interclube',
                'acronym': 'INT',
                'founded_year': 1976,
                'location': 'Luanda',
                'stadium_name': 'Estádio 22 de Junho',
                'primary_color': '#0000FF',
                'secondary_color': '#FFFFFF',
            },
            {
                'key': 'libolo',
                'name': 'Clube Recreativo Desportivo do Libolo',
                'short_name': 'Libolo',
                'acronym': 'LIB',
                'founded_year': 1942,
                'location': 'Libolo',
                'stadium_name': 'Estádio Municipal de Calulo',
                'primary_color': '#FF6600',
                'secondary_color': '#0000FF',
            },
            {
                'key': 'sagrada',
                'name': 'Grupo Desportivo Sagrada Esperança',
                'short_name': 'Sagrada',
                'acronym': 'SGE',
                'founded_year': 1976,
                'location': 'Dundo',
                'stadium_name': 'Estádio Sagrada Esperança',
                'primary_color': '#008000',
                'secondary_color': '#FFFFFF',
            },
            {
                'key': 'progresso',
                'name': 'Progresso Associação do Sambizanga',
                'short_name': 'Progresso',
                'acronym': 'PAS',
                'founded_year': 1975,
                'location': 'Luanda',
                'stadium_name': 'Estádio dos Coqueiros',
                'primary_color': '#FFFF00',
                'secondary_color': '#FF0000',
            },
            {
                'key': 'academica',
                'name': 'Académica Petróleos do Lobito',
                'short_name': 'Académica',
                'acronym': 'APL',
                'founded_year': 1915,
                'location': 'Lobito',
                'stadium_name': 'Estádio do Buraco',
                'primary_color': '#0000FF',
                'secondary_color': '#FFFF00',
            },
            {
                'key': 'huila',
                'name': 'Clube Desportivo da Huíla',
                'short_name': 'Desport. H.',
                'acronym': 'CDH',
                'founded_year': 1998,
                'location': 'Lubango',
                'stadium_name': 'Estádio do Ferroviário',
                'primary_color': '#FF0000',
                'secondary_color': '#FFFFFF',
            },
            {
                'key': 'maquis',
                'name': 'Futebol Clube Bravos do Maquis',
                'short_name': 'Bravos Maq.',
                'acronym': 'MAQ',
                'founded_year': 1983,
                'location': 'Luena',
                'stadium_name': 'Estádio Mundunduleno',
                'primary_color': '#008000',
                'secondary_color': '#FFFF00',
            },
            {
                'key': 'kabuscrop',
                'name': 'Kabuscorp Sport Clube do Palanca',
                'short_name': 'Kabuscorp',
                'acronym': 'KAB',
                'founded_year': 1994,
                'location': 'Luanda',
                'stadium_name': 'Estádio dos Coqueiros',
                'primary_color': '#FF0000',
                'secondary_color': '#FFFF00',
            },
            {
                'key': 'recreativo',
                'name': 'Clube Recreativo da Caála',
                'short_name': 'Recr. Caála',
                'acronym': 'CRC',
                'founded_year': 1944,
                'location': 'Caála',
                'stadium_name': 'Estádio Mártires da Canhala',
                'primary_color': '#0000FF',
                'secondary_color': '#FF0000',
            },
            {
                'key': 'benfica',
                'name': 'Sport Luanda e Benfica',
                'short_name': 'Benfica Lda',
                'acronym': 'SLB',
                'founded_year': 1922,
                'location': 'Luanda',
                'stadium_name': 'Estádio 11 de Novembro',
                'primary_color': '#FF0000',
                'secondary_color': '#FFFFFF',
            },
            {
                'key': 'lundasul',
                'name': 'Clube Desportivo da Lunda Sul',
                'short_name': 'Lunda Sul',
                'acronym': 'CDL',
                'founded_year': 2014,
                'location': 'Saurimo',
                'stadium_name': 'Estádio das Mangueiras',
                'primary_color': '#FFFF00',
                'secondary_color': '#008000',
            },
            {
                'key': 'wiliete',
                'name': 'Wiliete Sport Clube de Benguela',
                'short_name': 'Wiliete',
                'acronym': 'WSC',
                'founded_year': 2012,
                'location': 'Benguela',
                'stadium_name': 'Estádio de Ombaka',
                'primary_color': '#0000FF',
                'secondary_color': '#FFCC00',
            },
            {
                'key': 'santos',
                'name': 'Santos Futebol Clube de Angola',
                'short_name': 'Santos',
                'acronym': 'SFC',
                'founded_year': 2002,
                'location': 'Luanda',
                'stadium_name': 'Estádio dos Coqueiros',
                'primary_color': '#FFFFFF',
                'secondary_color': '#000000',
            },
            {
                'key': 'sportingc',
                'name': 'Sporting Clube de Cabinda',
                'short_name': 'Sporting C.',
                'acronym': 'SCC',
                'founded_year': 1922,
                'location': 'Cabinda',
                'stadium_name': 'Estádio do Tafe',
                'primary_color': '#008000',
                'secondary_color': '#FFFFFF',
            },
        ]

        for c in clubs_data:
            club, created = Club.objects.get_or_create(
                tenant=tenant,
                name=c['name'],
                defaults={
                    'acronym': c.get('acronym', ''),
                    'short_name': c.get('short_name', ''),
                    'founded_year': c['founded_year'],
                    'location': c['location'],
                    'stadium_name': c['stadium_name'],
                    'primary_color': c['primary_color'],
                    'secondary_color': c['secondary_color'],
                },
            )
            if not created:
                acronym = c.get('acronym')
                short_name = c.get('short_name')
                updated_fields = []
                if acronym is not None and club.acronym != acronym:
                    club.acronym = acronym
                    updated_fields.append('acronym')
                if short_name is not None and club.short_name != short_name:
                    club.short_name = short_name
                    updated_fields.append('short_name')
                if updated_fields:
                    club.save(update_fields=updated_fields)

        total_clubs = Club.objects.filter(tenant=tenant).count()
        self.stdout.write(self.style.SUCCESS(f'Seed de clubs de Angola executado para tenant {tenant.slug}: {total_clubs} clubs'))

