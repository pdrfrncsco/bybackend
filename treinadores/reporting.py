from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from django.utils import timezone

from .models import Treinador, HistoricoTreinador


@dataclass(frozen=True)
class TreinadorReport:
    treinador_id: str
    total_jogos: int
    total_vitorias: int
    total_empates: int
    total_derrotas: int
    percentual_vitorias: float
    tempo_medio_por_clube_dias: float
    historico_cronologico: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "treinadorId": self.treinador_id,
            "totalJogos": self.total_jogos,
            "totalVitorias": self.total_vitorias,
            "totalEmpates": self.total_empates,
            "totalDerrotas": self.total_derrotas,
            "percentualVitorias": self.percentual_vitorias,
            "tempoMedioPorClubeDias": self.tempo_medio_por_clube_dias,
            "historicoCronologico": self.historico_cronologico,
        }


def _days_between(start: date, end: date) -> int:
    if end < start:
        return 0
    return (end - start).days


def generate_treinador_report(treinador: Treinador) -> TreinadorReport:
    historico_qs = (
        HistoricoTreinador.objects.filter(treinador=treinador)
        .select_related("clube")
        .order_by("data_inicio", "id")
    )
    historico = list(historico_qs)

    total_jogos = sum(h.jogos for h in historico)
    total_vitorias = sum(h.vitorias for h in historico)
    total_empates = sum(h.empates for h in historico)
    total_derrotas = sum(h.derrotas for h in historico)

    percentual_vitorias = 0.0
    if total_jogos > 0:
        percentual_vitorias = (total_vitorias / total_jogos) * 100.0

    today = timezone.now().date()
    duracoes = []
    historico_cronologico: list[dict[str, Any]] = []

    for h in historico:
        fim = h.data_fim or today
        duracao = _days_between(h.data_inicio, fim)
        duracoes.append(duracao)
        historico_cronologico.append(
            {
                "historicoId": str(h.id),
                "clubeId": str(h.clube_id),
                "clubeNome": h.clube.name,
                "cargo": h.cargo,
                "dataInicio": h.data_inicio,
                "dataFim": h.data_fim,
                "jogos": h.jogos,
                "vitorias": h.vitorias,
                "empates": h.empates,
                "derrotas": h.derrotas,
                "conquistas": h.conquistas,
                "duracaoDias": duracao,
                "isAtual": h.data_fim is None,
            }
        )

    tempo_medio_por_clube_dias = 0.0
    if duracoes:
        tempo_medio_por_clube_dias = sum(duracoes) / float(len(duracoes))

    return TreinadorReport(
        treinador_id=str(treinador.id),
        total_jogos=total_jogos,
        total_vitorias=total_vitorias,
        total_empates=total_empates,
        total_derrotas=total_derrotas,
        percentual_vitorias=percentual_vitorias,
        tempo_medio_por_clube_dias=tempo_medio_por_clube_dias,
        historico_cronologico=historico_cronologico,
    )

