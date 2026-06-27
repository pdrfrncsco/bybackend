from django.utils import timezone
from django.db.models import Sum, Q
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from drf_spectacular.utils import extend_schema

from core.permissions import IsManager
from classificacoes.models import Standing
from jogadores.models import Player, PlayerHistory
from partidas.models import Match
from clubs.models import Club
from torneios.models import Tournament
from assinaturas.models import Subscription

from .models import ReportJob
from .serializers import (
    ReportDefinitionSerializer,
    ReportJobSerializer,
    GenerateReportSerializer,
)


FREE_REPORT_TYPES = {
    "standings",
    "calendar",
}


PRO_REPORT_TYPES = {
    "standings",
    "club_performance",
    "player_stats",
    "calendar",
    "squad_list",
}


REPORT_DEFINITIONS = [
    {
        "id": "standings",
        "label": "Classificação / Chaveamento",
        "description": "Tabela de classificação geral, grupos ou chaveamento.",
        "requires": ["tournament"],
        "supported_formats": ["pdf", "csv", "excel"],
    },
    {
        "id": "club_performance",
        "label": "Desempenho por Clube (Temporada)",
        "description": "Resumo de desempenho e histórico recente de um clube.",
        "requires": ["tournament", "club"],
        "supported_formats": ["pdf", "csv", "excel"],
    },
    {
        "id": "player_stats",
        "label": "Estatísticas de Jogadores (Torneio)",
        "description": "Ranking de jogadores com estatísticas ofensivas e disciplinares.",
        "requires": ["tournament"],
        "supported_formats": ["pdf", "csv", "excel"],
    },
    {
        "id": "individual_technical_sheet",
        "label": "Ficha Técnica Individual (Atleta)",
        "description": "Ficha resumida do atleta com histórico de temporadas.",
        "requires": ["player"],
        "supported_formats": ["pdf", "csv"],
    },
    {
        "id": "calendar",
        "label": "Calendário de Jogos",
        "description": "Calendário de jornadas e partidas do torneio.",
        "requires": ["tournament"],
        "supported_formats": ["pdf", "csv", "excel"],
    },
    {
        "id": "squad_list",
        "label": "Lista de Jogadores (Plantel)",
        "description": "Lista de inscrição oficial do plantel do clube.",
        "requires": ["club"],
        "supported_formats": ["pdf", "csv", "excel"],
    },
    {
        "id": "match_sheet",
        "label": "Ficha de Jogo (Oficial)",
        "description": "Ficha de jogo com equipas, resultado e eventos principais.",
        "requires": ["match"],
        "supported_formats": ["pdf", "csv"],
    },
]


class ReportJobViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsManager]
    serializer_class = ReportJobSerializer

    def get_queryset(self):
        user = self.request.user
        tenant = getattr(user, "tenant", None)
        qs = ReportJob.objects.all()
        if tenant:
            qs = qs.filter(tenant=tenant)
        return qs.filter(user=user)

    def _get_tenant_plan_type(self, tenant):
        if not tenant:
            return "free"
        subscription = (
            Subscription.objects.filter(
                subscriber_type="tenant",
                tenant=tenant,
                status="active",
            )
            .select_related("plan")
            .order_by("-start_date")
            .first()
        )
        if not subscription or not subscription.plan:
            return "free"
        plan_type = (subscription.plan.plan_type or "").lower()
        if plan_type in {"free", "pro", "premium"}:
            return plan_type
        return "free"

    def _ensure_report_permission(self, tenant, report_type):
        plan_type = self._get_tenant_plan_type(tenant)
        if plan_type == "premium":
            return
        if plan_type == "pro" and report_type in PRO_REPORT_TYPES:
            return
        if plan_type == "free" and report_type in FREE_REPORT_TYPES:
            return
        raise PermissionDenied("Recurso disponível em plano superior.")

    @extend_schema(
        responses=ReportDefinitionSerializer(many=True),
        tags=["Relatórios", "Admin/Manager Only"],
        description="Lista de tipos de relatórios disponíveis e respetivos requisitos. Requer utilizador com permissões de gestão (por exemplo, MANAGER ou ADMIN).",
    )
    @action(detail=False, methods=["get"], url_path="definitions")
    def definitions(self, request):
        def get_required_plan(report_id: str) -> str:
            if report_id in FREE_REPORT_TYPES:
                return "free"
            if report_id in PRO_REPORT_TYPES:
                return "pro"
            return "premium"

        data_with_plan = []
        for item in REPORT_DEFINITIONS:
            report_id = item["id"]
            item_with_plan = {
                **item,
                "required_plan": get_required_plan(report_id),
            }
            data_with_plan.append(item_with_plan)

        serializer = ReportDefinitionSerializer(data_with_plan, many=True)
        return Response(serializer.data)

    @extend_schema(
        request=GenerateReportSerializer,
        responses=ReportJobSerializer,
        tags=["Relatórios", "Admin/Manager Only"],
        description="Gera um relatório sob demanda com base no tipo, formato e parâmetros. Requer utilizador com permissões de gestão (por exemplo, MANAGER ou ADMIN).",
    )
    @action(detail=False, methods=["post"], url_path="generate")
    def generate(self, request):
        user = request.user
        tenant = getattr(user, "tenant", None)
        if not tenant:
            return Response(
                {"detail": "Utilizador sem tenant associado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = GenerateReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        report_type = data["report_type"]
        fmt = data["format"]
        params = data.get("params", {})

        self._ensure_report_permission(tenant, report_type)

        job = ReportJob.objects.create(
            tenant=tenant,
            user=user,
            report_type=report_type,
            format=fmt,
            status="pending",
            params=params,
        )

        try:
            content = self._build_report_content(tenant, report_type, params)
            filename = self._build_filename(report_type, fmt)
            content_file = ContentFile(content.encode("utf-8"))
            job.file.save(filename, content_file, save=False)
            job.status = "completed"
            job.error_message = ""
            job.save()
        except Exception as exc:
            job.status = "failed"
            job.error_message = str(exc)
            job.save()
            return Response(
                {"detail": "Erro ao gerar relatório."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        output_serializer = ReportJobSerializer(job, context={"request": request})
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        responses=ReportJobSerializer(many=True),
        tags=["Relatórios", "Admin/Manager Only"],
        description="Histórico de relatórios gerados pelo utilizador autenticado. Requer utilizador com permissões de gestão (por exemplo, MANAGER ou ADMIN).",
    )
    @action(detail=False, methods=["get"], url_path="history")
    def history(self, request):
        queryset = self.get_queryset()
        serializer = ReportJobSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data)

    def _build_filename(self, report_type, fmt):
        now = timezone.now().strftime("%Y%m%d_%H%M%S")
        return f"{report_type}_{now}.{ 'csv' if fmt == 'csv' else ('xlsx' if fmt == 'excel' else 'txt') }"

    def _build_report_content(self, tenant, report_type, params):
        if report_type == "standings":
            return self._build_standings_content(tenant, params)
        if report_type == "player_stats":
            return self._build_player_stats_content(tenant, params)
        if report_type == "calendar":
            return self._build_calendar_content(tenant, params)
        if report_type == "squad_list":
            return self._build_squad_list_content(tenant, params)
        if report_type == "match_sheet":
            return self._build_match_sheet_content(tenant, params)
        if report_type == "club_performance":
            return self._build_club_performance_content(tenant, params)
        if report_type == "individual_technical_sheet":
            return self._build_individual_sheet_content(tenant, params)
        return "report_type,info\nunknown,Tipo de relatório não suportado\n"

    def _build_standings_content(self, tenant, params):
        tournament_id = params.get("tournament")
        queryset = Standing.objects.filter(tenant=tenant)
        if tournament_id:
            queryset = queryset.filter(tournament_id=tournament_id)
        queryset = queryset.select_related("club").order_by("-points", "-goals_for")

        lines = ["club,played,wins,draws,losses,goals_for,goals_against,points"]
        for s in queryset:
            lines.append(
                f"{s.club.name},{s.played},{s.wins},{s.draws},{s.losses},{s.goals_for},{s.goals_against},{s.points}"
            )
        if len(lines) == 1:
            lines.append("Nenhum registo de classificação disponível para os filtros aplicados.,0,0,0,0,0,0,0")
        return "\n".join(lines)

    def _build_player_stats_content(self, tenant, params):
        tournament_id = params.get("tournament")
        min_goals = int(params.get("min_goals", 0))

        histories = PlayerHistory.objects.filter(player__tenant=tenant)
        if tournament_id:
            try:
                tournament = Tournament.objects.get(id=tournament_id, tenant=tenant)
                histories = histories.filter(season=tournament.season)
            except Tournament.DoesNotExist:
                histories = histories.none()

        aggregated = (
            histories.values("player_id", "player__name", "club__name")
            .annotate(
                goals=Sum("goals"),
                matches=Sum("matches"),
                assists=Sum("assists"),
                minutes=Sum("minutes"),
                yellow_cards=Sum("yellow_cards"),
                red_cards=Sum("red_cards"),
            )
            .order_by("-goals", "player__name")
        )
        if min_goals > 0:
            aggregated = aggregated.filter(goals__gte=min_goals)

        lines = [
            "player,club,matches,minutes,goals,assists,yellow_cards,red_cards",
        ]
        for row in aggregated:
            lines.append(
                f"{row['player__name']},{row['club__name'] or ''},{row['matches']},{row['minutes']},{row['goals']},{row['assists']},{row['yellow_cards']},{row['red_cards']}"
            )
        if len(lines) == 1:
            lines.append("Nenhum jogador encontrado para os filtros.,0,0,0,0,0,0,0")
        return "\n".join(lines)

    def _build_calendar_content(self, tenant, params):
        tournament_id = params.get("tournament")
        date_start = params.get("date_start")
        date_end = params.get("date_end")

        matches = Match.objects.filter(tenant=tenant)
        if tournament_id:
            matches = matches.filter(tournament_id=tournament_id)
        if date_start:
            matches = matches.filter(date__date__gte=date_start)
        if date_end:
            matches = matches.filter(date__date__lte=date_end)

        matches = matches.select_related("home_team", "away_team", "venue", "tournament").order_by("date")

        lines = ["date,time,home,away,stadium,round,tournament"]
        for m in matches:
            date_str = m.date.date().isoformat()
            time_str = m.date.time().strftime("%H:%M")
            lines.append(
                f"{date_str},{time_str},{m.home_team.name},{m.away_team.name},{getattr(m.venue, 'name', '')},{m.round},{getattr(m.tournament, 'name', '')}"
            )
        if len(lines) == 1:
            lines.append("Nenhum jogo encontrado para os filtros.,,, ,,,")
        return "\n".join(lines)

    def _build_squad_list_content(self, tenant, params):
        club_id = params.get("club")
        if not club_id:
            return "number,name,nickname,position,nationality\n"

        players = Player.objects.filter(tenant=tenant, club_id=club_id).order_by("number", "name")
        lines = ["number,name,nickname,position,nationality"]
        for p in players:
            lines.append(
                f"{p.number or ''},{p.name},{p.nickname},{p.position},{p.nationality}"
            )
        if len(lines) == 1:
            lines.append(",,Nenhum jogador encontrado,,,")
        return "\n".join(lines)

    def _build_match_sheet_content(self, tenant, params):
        match_id = params.get("match")
        if not match_id:
            return "field,value\nerror,Identificador de jogo não fornecido\n"

        try:
            match = Match.objects.select_related("home_team", "away_team", "venue", "tournament").get(
                id=match_id, tenant=tenant
            )
        except (Match.DoesNotExist, ValidationError, ValueError, TypeError):
            return "field,value\nerror,Jogo não encontrado\n"

        lines = [
            "field,value",
            f"tournament,{getattr(match.tournament, 'name', '')}",
            f"round,{match.round}",
            f"date,{match.date.date().isoformat()}",
            f"time,{match.date.time().strftime('%H:%M')}",
            f"stadium,{getattr(match.venue, 'name', '')}",
            f"home_team,{match.home_team.name}",
            f"away_team,{match.away_team.name}",
            f"home_score,{match.home_score if match.home_score is not None else ''}",
            f"away_score,{match.away_score if match.away_score is not None else ''}",
        ]
        return "\n".join(lines)

    def _build_club_performance_content(self, tenant, params):
        tournament_id = params.get("tournament")
        club_id = params.get("club")
        if not (tournament_id and club_id):
            return "metric,value\nerror,Torneio e clube são obrigatórios\n"

        matches = (
            Match.objects.filter(
                tenant=tenant,
                tournament_id=tournament_id,
                status="finished",
                home_score__isnull=False,
                away_score__isnull=False,
            )
            .filter(Q(home_team_id=club_id) | Q(away_team_id=club_id))
        )

        played = matches.count()
        wins = 0
        draws = 0
        losses = 0
        goals_for = 0
        goals_against = 0

        for m in matches:
            if m.home_team_id == club_id:
                gf = m.home_score or 0
                ga = m.away_score or 0
            else:
                gf = m.away_score or 0
                ga = m.home_score or 0
            goals_for += gf
            goals_against += ga
            if gf > ga:
                wins += 1
            elif gf == ga:
                draws += 1
            else:
                losses += 1

        points = wins * 3 + draws

        lines = [
            "metric,value",
            f"played,{played}",
            f"wins,{wins}",
            f"draws,{draws}",
            f"losses,{losses}",
            f"goals_for,{goals_for}",
            f"goals_against,{goals_against}",
            f"points,{points}",
        ]
        return "\n".join(lines)

    def _build_individual_sheet_content(self, tenant, params):
        player_id = params.get("player")
        if not player_id:
            return "field,value\nerror,Jogador não fornecido\n"

        try:
            player = Player.objects.select_related("club").get(id=player_id, tenant=tenant)
        except Player.DoesNotExist:
            return "field,value\nerror,Jogador não encontrado\n"

        history = PlayerHistory.objects.filter(player=player).aggregate(
            matches=Sum("matches"),
            goals=Sum("goals"),
            assists=Sum("assists"),
        )

        lines = [
            "field,value",
            f"name,{player.name}",
            f"club,{player.club.name if player.club else ''}",
            f"position,{player.position}",
            f"nationality,{player.nationality}",
            f"total_matches,{history.get('matches') or 0}",
            f"total_goals,{history.get('goals') or 0}",
            f"total_assists,{history.get('assists') or 0}",
        ]
        return "\n".join(lines)
