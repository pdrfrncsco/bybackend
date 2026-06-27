from datetime import date, timedelta

from django.db import IntegrityError
from django.test import TestCase

from core.models import Tenant
from clubs.models import Club
from .models import Treinador, HistoricoTreinador
from .reporting import generate_treinador_report


class TreinadoresModelsTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Liga Teste", slug="liga-teste")
        self.club1 = Club.objects.create(tenant=self.tenant, name="Clube A")
        self.club2 = Club.objects.create(tenant=self.tenant, name="Clube B")
        self.treinador = Treinador.objects.create(
            tenant=self.tenant,
            first_name="Carlos",
            last_name="Silva",
            nacionalidade="Angolana",
            data_nascimento=date(1980, 1, 1),
            estilo_jogo="Posse e pressão alta",
            biografia="Treinador com foco em formação.",
        )

    def test_unique_current_historico_constraint(self):
        HistoricoTreinador.objects.create(
            treinador=self.treinador,
            clube=self.club1,
            cargo="Treinador Principal",
            data_inicio=date(2024, 1, 1),
            data_fim=None,
            jogos=10,
            vitorias=6,
            empates=2,
            derrotas=2,
            conquistas="",
        )

        with self.assertRaises(IntegrityError):
            HistoricoTreinador.objects.create(
                treinador=self.treinador,
                clube=self.club2,
                cargo="Treinador Principal",
                data_inicio=date(2025, 1, 1),
                data_fim=None,
                jogos=5,
                vitorias=2,
                empates=1,
                derrotas=2,
                conquistas="",
            )

    def test_generate_report_aggregates_fields(self):
        start1 = date.today() - timedelta(days=120)
        end1 = date.today() - timedelta(days=60)
        start2 = date.today() - timedelta(days=59)

        HistoricoTreinador.objects.create(
            treinador=self.treinador,
            clube=self.club1,
            cargo="Treinador Principal",
            data_inicio=start1,
            data_fim=end1,
            jogos=10,
            vitorias=5,
            empates=3,
            derrotas=2,
            conquistas="Taça",
        )
        HistoricoTreinador.objects.create(
            treinador=self.treinador,
            clube=self.club2,
            cargo="Treinador Principal",
            data_inicio=start2,
            data_fim=None,
            jogos=4,
            vitorias=3,
            empates=0,
            derrotas=1,
            conquistas="",
        )

        report = generate_treinador_report(self.treinador)

        self.assertEqual(report.total_jogos, 14)
        self.assertEqual(report.total_vitorias, 8)
        self.assertGreaterEqual(report.percentual_vitorias, 0.0)
        self.assertLessEqual(report.percentual_vitorias, 100.0)
        self.assertEqual(len(report.historico_cronologico), 2)

