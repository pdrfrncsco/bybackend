from django.core.management.base import BaseCommand
from core.models import Tenant


class Command(BaseCommand):
    help = 'Gera 16 organizações públicas (Tenants) de exemplo'

    def handle(self, *args, **options):
        organizations_data = [
            {
                'slug': 'federacao-angolana-futebol',
                'name': 'Federação Angolana de Futebol',
                'type': 'federation',
                'country': 'Angola',
                'location': 'Luanda',
                'primary_color': '#22c55e',
                'secondary_color': '#0f172a',
                'description': 'Entidade máxima do futebol em Angola.',
                'is_public': True,
                'verified': True,
            },
            {
                'slug': 'liga-angolana',
                'name': 'Liga Angolana de Futebol',
                'type': 'league',
                'country': 'Angola',
                'location': 'Luanda',
                'primary_color': '#0ea5e9',
                'secondary_color': '#020617',
                'description': 'Liga profissional de clubs angolanos.',
                'is_public': True,
                'verified': True,
            },
            {
                'slug': 'assoc-luanda',
                'name': 'Associação de Futebol de Luanda',
                'type': 'association',
                'country': 'Angola',
                'location': 'Luanda',
                'primary_color': '#f97316',
                'secondary_color': '#1e293b',
                'description': 'Organiza competições regionais em Luanda.',
                'is_public': True,
                'verified': True,
            },
            {
                'slug': 'assoc-benguela',
                'name': 'Associação de Futebol de Benguela',
                'type': 'association',
                'country': 'Angola',
                'location': 'Benguela',
                'primary_color': '#22c55e',
                'secondary_color': '#1e293b',
                'description': 'Associação regional responsável pelo futebol em Benguela.',
                'is_public': True,
                'verified': False,
            },
            {
                'slug': 'liga-escolar-luanda',
                'name': 'Liga Escolar de Luanda',
                'type': 'school',
                'country': 'Angola',
                'location': 'Luanda',
                'primary_color': '#3b82f6',
                'secondary_color': '#111827',
                'description': 'Competição escolar de Luanda com foco em formação.',
                'is_public': True,
                'verified': False,
            },
            {
                'slug': 'liga-escolar-benguela',
                'name': 'Liga Escolar de Benguela',
                'type': 'school',
                'country': 'Angola',
                'location': 'Benguela',
                'primary_color': '#4ade80',
                'secondary_color': '#052e16',
                'description': 'Liga escolar para clubs de formação em Benguela.',
                'is_public': True,
                'verified': False,
            },
            {
                'slug': 'torneio-provincial-huila',
                'name': 'Torneio Provincial da Huíla',
                'type': 'tournament',
                'country': 'Angola',
                'location': 'Lubango',
                'primary_color': '#f59e0b',
                'secondary_color': '#1e293b',
                'description': 'Torneio provincial realizado na Huíla.',
                'is_public': True,
                'verified': False,
            },
            {
                'slug': 'torneio-provincial-huambo',
                'name': 'Torneio Provincial do Huambo',
                'type': 'tournament',
                'country': 'Angola',
                'location': 'Huambo',
                'primary_color': '#ef4444',
                'secondary_color': '#111827',
                'description': 'Competição provincial de clubs do Huambo.',
                'is_public': True,
                'verified': False,
            },
            {
                'slug': 'liga-amadora-luanda',
                'name': 'Liga Amadora de Luanda',
                'type': 'amateur',
                'country': 'Angola',
                'location': 'Luanda',
                'primary_color': '#a855f7',
                'secondary_color': '#1e293b',
                'description': 'Liga amadora voltada para clubs de bairro em Luanda.',
                'is_public': True,
                'verified': False,
            },
            {
                'slug': 'liga-amadora-benguela',
                'name': 'Liga Amadora de Benguela',
                'type': 'amateur',
                'country': 'Angola',
                'location': 'Benguela',
                'primary_color': '#22c55e',
                'secondary_color': '#0f172a',
                'description': 'Liga amadora com clubs da província de Benguela.',
                'is_public': True,
                'verified': False,
            },
            {
                'slug': 'federacao-provincial-huila',
                'name': 'Federação Provincial da Huíla',
                'type': 'federation',
                'country': 'Angola',
                'location': 'Lubango',
                'primary_color': '#0ea5e9',
                'secondary_color': '#020617',
                'description': 'Entidade que coordena o futebol na província da Huíla.',
                'is_public': True,
                'verified': False,
            },
            {
                'slug': 'federacao-provincial-benguela',
                'name': 'Federação Provincial de Benguela',
                'type': 'federation',
                'country': 'Angola',
                'location': 'Benguela',
                'primary_color': '#f97316',
                'secondary_color': '#111827',
                'description': 'Federação responsável pelo futebol na província de Benguela.',
                'is_public': True,
                'verified': False,
            },
            {
                'slug': 'liga-distrital-cazenga',
                'name': 'Liga Distrital do Cazenga',
                'type': 'league',
                'country': 'Angola',
                'location': 'Luanda - Cazenga',
                'primary_color': '#22c55e',
                'secondary_color': '#0f172a',
                'description': 'Liga distrital focada em clubs do Cazenga.',
                'is_public': True,
                'verified': False,
            },
            {
                'slug': 'liga-distrital-viana',
                'name': 'Liga Distrital de Viana',
                'type': 'league',
                'country': 'Angola',
                'location': 'Luanda - Viana',
                'primary_color': '#3b82f6',
                'secondary_color': '#020617',
                'description': 'Liga local que integra clubs de Viana.',
                'is_public': True,
                'verified': False,
            },
            {
                'slug': 'copa-sub20-angola',
                'name': 'Copa Sub-20 de Angola',
                'type': 'tournament',
                'country': 'Angola',
                'location': 'Várias cidades',
                'primary_color': '#22c55e',
                'secondary_color': '#111827',
                'description': 'Competição nacional de clubs Sub-20.',
                'is_public': True,
                'verified': False,
            },
            {
                'slug': 'copa-sub17-angola',
                'name': 'Copa Sub-17 de Angola',
                'type': 'tournament',
                'country': 'Angola',
                'location': 'Várias cidades',
                'primary_color': '#f97316',
                'secondary_color': '#0f172a',
                'description': 'Competição nacional de clubs Sub-17.',
                'is_public': True,
                'verified': False,
            },
        ]

        total_created = 0
        total_updated = 0

        for data in organizations_data:
            slug = data['slug']
            defaults = {
                'name': data['name'],
                'type': data['type'],
                'country': data['country'],
                'location': data['location'],
                'primary_color': data['primary_color'],
                'secondary_color': data['secondary_color'],
                'description': data['description'],
                'is_public': data['is_public'],
                'verified': data['verified'],
            }

            tenant, created = Tenant.objects.update_or_create(
                slug=slug,
                defaults=defaults,
            )

            if created:
                total_created += 1
            else:
                total_updated += 1

        total = Tenant.objects.filter(
            slug__in=[o['slug'] for o in organizations_data]
        ).count()

        self.stdout.write(
            self.style.SUCCESS(
                f'Seed de organizações executado: {total} tenants, '
                f'{total_created} criados, {total_updated} atualizados'
            )
        )

