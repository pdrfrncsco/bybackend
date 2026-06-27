from datetime import date

from django.core.management.base import BaseCommand, CommandError

from core.models import Tenant
from clubs.models import Club
from treinadores.models import Treinador, HistoricoTreinador, LicencaTreinador


class Command(BaseCommand):
    help = 'Gera treinadores de exemplo para um tenant'

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

        clubs = list(Club.objects.filter(tenant=tenant).order_by('name'))
        cargos = [choice[0] for choice in HistoricoTreinador.CARGO_CHOICES]

        first_names = [
            'João',
            'Carlos',
            'Miguel',
            'André',
            'Paulo',
            'Rui',
            'Pedro',
            'Fábio',
        ]
        last_names = [
            'Silva',
            'Ferreira',
            'Santos',
            'Lopes',
            'Costa',
            'Gomes',
            'Pereira',
            'Almeida',
        ]
        nacionalidades = [
            'Angolana',
            'Portuguesa',
            'Brasileira',
            'Moçambicana',
        ]
        estilos = [
            'Estilo ofensivo com pressão alta e construção desde trás.',
            'Equilíbrio entre organização defensiva e transições rápidas.',
            'Foco em posse de bola e controlo de ritmo.',
            'Jogo direto com forte presença física.',
        ]

        total_created = 0
        total_updated = 0
        total_hist = 0
        total_lic = 0

        for i in range(1, count + 1):
            first_name = first_names[(i - 1) % len(first_names)]
            last_name = last_names[((i - 1) // len(first_names)) % len(last_names)]
            nacionalidade = nacionalidades[(i - 1) % len(nacionalidades)]
            estilo_jogo = estilos[(i - 1) % len(estilos)]

            birth_year = 1965 + ((i - 1) % 20)
            birth_month = ((i - 1) % 12) + 1
            birth_day = ((i - 1) % 28) + 1
            data_nascimento = date(birth_year, birth_month, birth_day)

            biografia = (
                f'{first_name} {last_name} é um treinador gerado automaticamente para o tenant '
                f'{tenant.slug}, com experiência em competições locais e regionais.'
            )

            defaults = {
                'nacionalidade': nacionalidade,
                'data_nascimento': data_nascimento,
                'estilo_jogo': estilo_jogo,
                'biografia': biografia,
            }

            treinador, created = Treinador.objects.update_or_create(
                tenant=tenant,
                first_name=first_name,
                last_name=last_name,
                defaults=defaults,
            )

            if created:
                total_created += 1
            else:
                total_updated += 1

            if clubs:
                club = clubs[(i - 1) % len(clubs)]
                cargo = cargos[(i - 1) % len(cargos)]

                start_year = 2020 - ((i - 1) % 4)
                data_inicio = date(start_year, 8, 1)

                historico_defaults = {
                    'data_fim': None,
                    'jogos': 0,
                    'vitorias': 0,
                    'empates': 0,
                    'derrotas': 0,
                    'conquistas': '',
                }

                HistoricoTreinador.objects.update_or_create(
                    treinador=treinador,
                    clube=club,
                    cargo=cargo,
                    data_inicio=data_inicio,
                    defaults=historico_defaults,
                )
                total_hist += 1

            licenca_nome = 'Licença CAF A' if i % 3 == 0 else 'Licença CAF B'
            entidade = 'CAF'
            emissao_year = 2015 + ((i - 1) % 8)
            data_emissao = date(emissao_year, 1, 15)
            data_validade = date(emissao_year + 3, 1, 15)

            licenca_defaults = {
                'data_validade': data_validade,
            }

            LicencaTreinador.objects.update_or_create(
                treinador=treinador,
                nome=licenca_nome,
                entidade=entidade,
                data_emissao=data_emissao,
                defaults=licenca_defaults,
            )
            total_lic += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Seed de treinadores executado para tenant {tenant.slug}: '
                f'{count} perfis, {total_created} criados, {total_updated} atualizados, '
                f'{total_hist} históricos, {total_lic} licenças'
            )
        )

