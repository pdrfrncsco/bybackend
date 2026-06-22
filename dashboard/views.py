from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, serializers
from drf_spectacular.utils import inline_serializer, extend_schema
from django.utils import timezone
from django.db.models import Count, Sum, F, Q, Case, When, IntegerField
from django.db.models.functions import TruncMonth
from datetime import timedelta

from core.permissions import IsManager
from clubes.models import Club
from jogadores.models import Player, PlayerHistory
from torneios.models import Tournament
from partidas.models import Match
from news.models import NewsArticle
from assinaturas.models import Subscription
from usuarios.models import User


DashboardKpisSerializer = inline_serializer(
    name="DashboardKpis",
    fields={
        "total_clubs": serializers.IntegerField(),
        "total_players": serializers.IntegerField(),
        "total_news": serializers.IntegerField(),
        "active_tournaments": serializers.IntegerField(),
        "tournaments_upcoming": serializers.IntegerField(),
        "tournaments_completed": serializers.IntegerField(),
        "matches_finished": serializers.IntegerField(),
        "matches_scheduled": serializers.IntegerField(),
        "matches_live": serializers.IntegerField(),
        "total_matches": serializers.IntegerField(),
        "matches_today": serializers.IntegerField(),
        "players_this_month": serializers.IntegerField(),
        "players_last_month": serializers.IntegerField(),
        "goals_total": serializers.IntegerField(),
        "avg_goals_per_match": serializers.FloatField(),
        "organization_subscribers": serializers.IntegerField(),
        "total_revenue": serializers.DecimalField(max_digits=12, decimal_places=2),
        "avg_subscribers_per_tournament": serializers.FloatField(),
    },
)

DashboardTournamentSummarySerializer = inline_serializer(
    name="DashboardTournamentSummary",
    fields={
        "id": serializers.CharField(),
        "name": serializers.CharField(),
        "status": serializers.CharField(),
        "progress": serializers.IntegerField(),
        "teams": serializers.IntegerField(),
        "logo": serializers.CharField(allow_null=True),
    },
)

DashboardTopClubSerializer = inline_serializer(
    name="DashboardTopClub",
    fields={
        "id": serializers.CharField(), 
        "name": serializers.CharField(), 
        "players": serializers.IntegerField(),
        "acronym": serializers.CharField(allow_blank=True),
        "logo": serializers.CharField(allow_null=True),
        "goals": serializers.IntegerField(),
    },
)

DashboardTopScorerSerializer = inline_serializer(
    name="DashboardTopScorer",
    fields={
        "id": serializers.CharField(),
        "name": serializers.CharField(),
        "nickname": serializers.CharField(allow_blank=True),
        "club": serializers.CharField(),
        "club_logo": serializers.CharField(allow_null=True),
        "avatar": serializers.CharField(allow_null=True),
        "goals": serializers.IntegerField(),
    },
)

DashboardMatchSerializer = inline_serializer(
    name="DashboardMatch",
    fields={
        "id": serializers.CharField(),
        "tournament": serializers.CharField(),
        "status": serializers.CharField(),
        "date": serializers.DateTimeField(),
        "home_name": serializers.CharField(),
        "home_logo": serializers.CharField(allow_null=True),
        "home_score": serializers.IntegerField(allow_null=True),
        "away_name": serializers.CharField(),
        "away_logo": serializers.CharField(allow_null=True),
        "away_score": serializers.IntegerField(allow_null=True),
    },
)

DashboardOverviewResponseSerializer = inline_serializer(
    name="DashboardOverviewResponse",
    fields={
        "kpis": DashboardKpisSerializer,
        "tournaments": serializers.JSONField(),
        "top_clubs_by_players": serializers.JSONField(),  # Mantendo nome legado por compatibilidade
        "top_scorers": serializers.JSONField(),
        "goals_evolution": serializers.JSONField(),
        "live_matches": serializers.JSONField(),
        "upcoming_matches": serializers.JSONField(),
    },
)

PublicStatsSerializer = inline_serializer(
    name="PublicStatsResponse",
    fields={
        "total_clubs": serializers.IntegerField(),
        "total_players": serializers.IntegerField(),
        "active_tournaments": serializers.IntegerField(),
        "total_matches": serializers.IntegerField(),
    },
)


class DashboardOverviewView(APIView):
    permission_classes = [IsManager]

    @extend_schema(
        responses=DashboardOverviewResponseSerializer,
        tags=["Dashboard", "Admin/Manager Only"],
        description="Requer role MANAGER ou ADMIN."
    )
    def get(self, request):
        user = request.user
        tenant = getattr(user, "tenant", None)

        clubs_qs = Club.objects.all()
        players_qs = Player.objects.all()
        tournaments_qs = Tournament.objects.all()
        matches_qs = Match.objects.all()
        news_qs = NewsArticle.objects.all()

        if tenant:
            clubs_qs = clubs_qs.filter(tenant=tenant)
            players_qs = players_qs.filter(tenant=tenant)
            tournaments_qs = tournaments_qs.filter(tenant=tenant)
            matches_qs = matches_qs.filter(tenant=tenant)
            news_qs = news_qs.filter(tenant=tenant)

        total_clubs = clubs_qs.count()
        total_players = players_qs.count()
        total_news = news_qs.count()
        active_tournaments = tournaments_qs.filter(status="active").count()
        tournaments_upcoming = tournaments_qs.filter(status="upcoming").count()
        tournaments_completed = tournaments_qs.filter(status="completed").count()

        matches_scheduled = matches_qs.filter(status="scheduled").count()
        matches_live = matches_qs.filter(status="live").count()
        matches_finished = matches_qs.filter(status="finished").count()
        total_matches = matches_qs.count()

        now = timezone.now()
        start_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_start = (start_month - timedelta(days=1)).replace(day=1)

        players_this_month = players_qs.filter(joined_date__gte=start_month).count()
        players_last_month = players_qs.filter(joined_date__gte=last_month_start, joined_date__lt=start_month).count()

        matches_today = matches_qs.filter(date__date=now.date()).count()

        finished_matches_qs = matches_qs.filter(status="finished")
        goals_total = 0
        for m in finished_matches_qs:
            if m.home_score is not None:
                goals_total += m.home_score
            if m.away_score is not None:
                goals_total += m.away_score
        avg_goals_per_match = 0
        if finished_matches_qs.exists():
            avg_goals_per_match = round(goals_total / finished_matches_qs.count(), 2)

        if tenant:
            organization_subscribers = tenant.subscribers.count()
            revenue_agg = Subscription.objects.filter(
                organization=tenant,
                status__in=['active', 'expired']
            ).aggregate(total=Sum('organizer_share'))
            total_revenue = revenue_agg['total'] or 0
        else:
            organization_subscribers = (
                User.objects.filter(subscriptions__isnull=False).distinct().count()
            )
            revenue_agg = Subscription.objects.filter(
                status__in=['active', 'expired']
            ).aggregate(total=Sum('organizer_share'))
            total_revenue = revenue_agg['total'] or 0

        tournaments_count = tournaments_qs.count()
        avg_subscribers_per_tournament = 0.0
        if tournaments_count > 0 and organization_subscribers > 0:
            avg_subscribers_per_tournament = round(
                organization_subscribers / tournaments_count, 2
            )

        tournaments_summary = []
        for t in tournaments_qs.order_by("-created_at")[:5]:
            if t.status == "upcoming":
                status_label = "Inscrições"
            elif t.status == "completed":
                status_label = "Finalizado"
            else:
                status_label = "Em andamento"

            tournaments_summary.append(
                {
                    "id": str(t.id),
                    "name": t.name,
                    "status": status_label,
                    "progress": t.progress,
                    "teams": t.clubs.count(),
                    "logo": t.logo.url if t.logo else None,
                }
            )

        # Top clubes por gols (gols a partir do histórico + total de jogadores por clube)
        top_clubs_by_players = []

        players_per_club = (
            players_qs.filter(club__in=clubs_qs, club__isnull=False)
            .values("club_id")
            .annotate(players_count=Count("id"))
        )
        players_per_club_map = {row["club_id"]: row["players_count"] for row in players_per_club}

        top_clubs_stats_qs = (
            PlayerHistory.objects.filter(club__in=clubs_qs, club__isnull=False)
            .values("club_id", "club__name", "club__acronym", "club__logo")
            .annotate(
                goals=Sum("goals"),
            )
            .order_by("-goals", "club__name")[:5]
        )
        for row in top_clubs_stats_qs:
            club_id = row["club_id"]
            club_logo = row["club__logo"]
            top_clubs_by_players.append(
                {
                    "id": str(club_id),
                    "name": row["club__name"],
                    "players": int(players_per_club_map.get(club_id, 0)),
                    "acronym": row["club__acronym"] or "",
                    "logo": club_logo.url if hasattr(club_logo, "url") else None,
                    "goals": int(row["goals"] or 0),
                }
            )

        # Top marcadores (por gols) com dados enriquecidos
        top_scorers = []
        player_history_qs = PlayerHistory.objects.all()
        if tenant:
            player_history_qs = player_history_qs.filter(player__tenant=tenant)

        top_scorers_data = (
            player_history_qs.values("player_id")
            .annotate(goals=Sum("goals"))
            .order_by("-goals")[:5]
        )

        player_ids = [item["player_id"] for item in top_scorers_data]
        players = Player.objects.filter(id__in=player_ids).select_related("club")
        players_map = {p.id: p for p in players}

        for item in top_scorers_data:
            player = players_map.get(item["player_id"])
            if player:
                top_scorers.append(
                    {
                        "id": str(player.id),
                        "name": player.name,
                        "nickname": player.nickname,
                        "club": player.club.name if player.club else "",
                        "club_logo": player.club.logo.url if player.club and player.club.logo else None,
                        "avatar": player.avatar.url if player.avatar else None,
                        "goals": int(item["goals"] or 0),
                    }
                )

        # Gols por competição (agregados por torneio)
        goals_evolution = []
        goals_by_tournament_qs = (
            matches_qs.filter(status="finished")
            .values("tournament_id", "tournament__name")
            .annotate(
                goals=Sum(
                    (F("home_score") + F("away_score")),
                    output_field=IntegerField(),
                )
            )
            .order_by("-goals")[:5]
        )
        for row in goals_by_tournament_qs:
            goals_evolution.append(
                {
                    "tournament_name": row["tournament__name"] or "Sem torneio",
                    "data": [
                        {
                            "period": "Total",
                            "goals": int(row["goals"] or 0),
                        }
                    ],
                }
            )

        # Listas de jogos ao vivo e próximos jogos
        live_matches = []
        live_matches_qs = (
            matches_qs.filter(status="live")
            .select_related("home_team", "away_team", "tournament")
            .order_by("date")[:3]
        )
        for m in live_matches_qs:
            live_matches.append(
                {
                    "id": str(m.id),
                    "tournament": m.tournament.name if m.tournament else "",
                    "status": m.status,
                    "date": m.date,
                    "home_name": m.home_team.name,
                    "home_logo": m.home_team.logo.url if m.home_team.logo else None,
                    "home_score": m.home_score,
                    "away_name": m.away_team.name,
                    "away_logo": m.away_team.logo.url if m.away_team.logo else None,
                    "away_score": m.away_score,
                }
            )

        upcoming_matches = []
        upcoming_matches_qs = (
            matches_qs.filter(status="scheduled", date__gte=now)
            .select_related("home_team", "away_team", "tournament")
            .order_by("date")[:3]
        )
        for m in upcoming_matches_qs:
            upcoming_matches.append(
                {
                    "id": str(m.id),
                    "tournament": m.tournament.name if m.tournament else "",
                    "status": m.status,
                    "date": m.date,
                    "home_name": m.home_team.name,
                    "home_logo": m.home_team.logo.url if m.home_team.logo else None,
                    "home_score": m.home_score,
                    "away_name": m.away_team.name,
                    "away_logo": m.away_team.logo.url if m.away_team.logo else None,
                    "away_score": m.away_score,
                }
            )

        data = {
            "kpis": {
                "total_clubs": total_clubs,
                "total_players": total_players,
                "total_news": total_news,
                "active_tournaments": active_tournaments,
                "tournaments_upcoming": tournaments_upcoming,
                "tournaments_completed": tournaments_completed,
                "matches_finished": matches_finished,
                "matches_scheduled": matches_scheduled,
                "matches_live": matches_live,
                "total_matches": total_matches,
                "matches_today": matches_today,
                "players_this_month": players_this_month,
                "players_last_month": players_last_month,
                "goals_total": goals_total,
                "avg_goals_per_match": avg_goals_per_match,
                "organization_subscribers": organization_subscribers,
                "total_revenue": total_revenue,
                "avg_subscribers_per_tournament": avg_subscribers_per_tournament,
            },
            "tournaments": tournaments_summary,
            "top_clubs_by_players": top_clubs_by_players,
            "top_scorers": top_scorers,
            "goals_evolution": goals_evolution,
            "live_matches": live_matches,
            "upcoming_matches": upcoming_matches,
        }

        return Response(data)


class PublicStatsView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        responses=PublicStatsSerializer,
        tags=["Public"],
        description="Estatísticas globais públicas da plataforma (sem autenticação).",
    )
    def get(self, request):
        total_clubs = Club.objects.count()
        total_players = Player.objects.count()
        active_tournaments = Tournament.objects.filter(status="active").count()
        total_matches = Match.objects.count()

        data = {
            "total_clubs": total_clubs,
            "total_players": total_players,
            "active_tournaments": active_tournaments,
            "total_matches": total_matches,
        }

        return Response(data)
