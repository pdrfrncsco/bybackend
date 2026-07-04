from datetime import timedelta

from django.db.models import Count, OuterRef, Q, Subquery, Sum
from django.db.models.functions import Coalesce, TruncMonth
from django.utils import timezone

from clubs.models import Club
from competitions.constants import CompetitionStatus
from competitions.models import Competition, Match, MatchEvent
from media_assets.constants import AssetCategory, OwnerType
from media_assets.services import MediaAssetService
from organizations.models import OrganizationSubscription
from players.models import Player, PlayerRegistration


class DashboardAnalyticsSelector:
    GOAL_EVENT_TYPES = [
        MatchEvent.EventType.GOAL,
        MatchEvent.EventType.OWN_GOAL,
        MatchEvent.EventType.PENALTY_SCORED,
    ]
    MONTH_LABELS = {
        1: "JAN",
        2: "FEV",
        3: "MAR",
        4: "ABR",
        5: "MAI",
        6: "JUN",
        7: "JUL",
        8: "AGO",
        9: "SET",
        10: "OUT",
        11: "NOV",
        12: "DEZ",
    }

    @classmethod
    def get_public_stats(cls) -> dict:
        competitions = Competition.objects.all()
        registrations = PlayerRegistration.objects.all()

        return {
            "total_clubs": Club.objects.count(),
            "total_players": cls._count_distinct_players(registrations),
            "active_tournaments": competitions.filter(status=CompetitionStatus.ACTIVE).count(),
            "total_matches": Match.objects.count(),
        }

    @classmethod
    def get_overview(cls, *, tenant=None) -> dict:
        clubs = Club.objects.all()
        competitions = Competition.objects.all()
        matches = Match.objects.all()
        events = MatchEvent.objects.all()
        registrations = PlayerRegistration.objects.all()
        subscriptions = OrganizationSubscription.objects.filter(is_active=True)

        if tenant is not None:
            clubs = clubs.filter(tenant=tenant)
            competitions = competitions.filter(tenant=tenant)
            matches = matches.filter(tenant=tenant)
            events = events.filter(tenant=tenant)
            registrations = registrations.filter(tenant=tenant)
            subscriptions = subscriptions.filter(tenant=tenant)

        total_players = cls._count_distinct_players(registrations)
        if tenant is None and total_players == 0:
            total_players = Player.objects.filter(status=Player.PlayerStatus.ACTIVE).count()

        total_tournaments = competitions.count()
        matches_finished = matches.filter(status=Match.MatchStatus.FINISHED).count()
        goals_total = events.filter(event_type__in=cls.GOAL_EVENT_TYPES).count()
        subscribers_count = subscriptions.count()
        today = timezone.localdate()

        players_this_month = registrations.filter(
            joined_date__year=today.year,
            joined_date__month=today.month,
        ).count()

        previous_month_date = today.replace(day=1) - timedelta(days=1)
        players_last_month = registrations.filter(
            joined_date__year=previous_month_date.year,
            joined_date__month=previous_month_date.month,
        ).count()

        avg_goals_per_match = round(goals_total / matches_finished, 2) if matches_finished else 0.0
        avg_subscribers_per_tournament = round(subscribers_count / total_tournaments, 2) if total_tournaments else 0.0

        return {
            "kpis": {
                "total_clubs": clubs.count(),
                "total_players": total_players,
                "total_news": 0,
                "active_tournaments": competitions.filter(status=CompetitionStatus.ACTIVE).count(),
                "tournaments_upcoming": competitions.filter(status=CompetitionStatus.DRAFT).count(),
                "tournaments_completed": competitions.filter(status=CompetitionStatus.COMPLETED).count(),
                "matches_finished": matches_finished,
                "matches_scheduled": matches.filter(status=Match.MatchStatus.SCHEDULED).count(),
                "matches_live": matches.filter(status=Match.MatchStatus.LIVE).count(),
                "total_matches": matches.count(),
                "matches_today": matches.filter(match_date__date=today).count(),
                "players_this_month": players_this_month,
                "players_last_month": players_last_month,
                "goals_total": goals_total,
                "avg_goals_per_match": avg_goals_per_match,
                "organization_subscribers": subscribers_count,
                "total_revenue": 0,
                "avg_subscribers_per_tournament": avg_subscribers_per_tournament,
            },
            "tournaments": cls._build_tournament_summaries(competitions),
            "top_clubs_by_players": cls._build_top_clubs(clubs),
            "top_scorers": cls._build_top_scorers(registrations),
            "goals_evolution": cls._build_goals_evolution(competitions, events),
            "live_matches": cls._build_matches(matches.filter(status=Match.MatchStatus.LIVE)[:5]),
            "upcoming_matches": cls._build_matches(
                matches.filter(status=Match.MatchStatus.SCHEDULED).order_by("match_date")[:5]
            ),
        }

    @staticmethod
    def _count_distinct_players(registrations) -> int:
        return registrations.values("player_id").distinct().count()

    @classmethod
    def _build_tournament_summaries(cls, competitions):
        queryset = competitions.annotate(
            teams_count=Count("registrations__club", distinct=True),
            matches_count=Count("matches", distinct=True),
            finished_matches_count=Count(
                "matches",
                filter=Q(matches__status=Match.MatchStatus.FINISHED),
                distinct=True,
            ),
        ).order_by("-created_at")[:5]

        summaries = []
        for competition in queryset:
            teams = competition.teams_count or cls._fallback_team_count(competition)
            if competition.status == CompetitionStatus.COMPLETED:
                progress = 100
            elif competition.matches_count:
                progress = round((competition.finished_matches_count / competition.matches_count) * 100)
            else:
                progress = 0

            summaries.append(
                {
                    "id": competition.id,
                    "name": competition.name,
                    "status": competition.get_status_display(),
                    "progress": progress,
                    "teams": teams,
                    "logo": cls._get_usage_url(
                        owner_type=OwnerType.COMPETITION,
                        owner_id=competition.id,
                    ),
                }
            )

        return summaries

    @staticmethod
    def _fallback_team_count(competition: Competition) -> int:
        club_ids = set()
        for home_club_id, away_club_id in Match.objects.filter(competition=competition).values_list(
            "home_club_id",
            "away_club_id",
        ):
            if home_club_id:
                club_ids.add(home_club_id)
            if away_club_id:
                club_ids.add(away_club_id)
        return len(club_ids)

    @classmethod
    def _build_top_clubs(cls, clubs):
        queryset = clubs.annotate(
            players_count=Count("player_registrations__player", distinct=True),
            goals_total=Coalesce(Sum("player_registrations__goals"), 0),
        ).order_by("-players_count", "-goals_total", "name")[:5]

        items = []
        for club in queryset:
            items.append(
                {
                    "id": club.id,
                    "name": club.name,
                    "players": club.players_count,
                    "acronym": club.short_name or cls._build_acronym(club.name),
                    "logo": cls._get_usage_url(
                        owner_type=OwnerType.CLUB,
                        owner_id=club.id,
                    ),
                    "goals": int(club.goals_total or 0),
                }
            )
        return items

    @classmethod
    def _build_top_scorers(cls, registrations):
        scoped_registrations = registrations.filter(goals__gt=0)
        latest_registration = scoped_registrations.filter(player_id=OuterRef("player_id")).order_by(
            "-joined_date", "-created_at"
        )

        rows = (
            scoped_registrations.values(
                "player_id",
                "player__first_name",
                "player__last_name",
                "player__avatar",
            )
            .annotate(
                goals=Coalesce(Sum("goals"), 0),
                club_name=Subquery(latest_registration.values("club__name")[:1]),
                club_id=Subquery(latest_registration.values("club_id")[:1]),
            )
            .order_by("-goals", "player__first_name", "player__last_name")[:5]
        )

        scorers = []
        for row in rows:
            club_id = row.get("club_id")
            scorers.append(
                {
                    "id": row["player_id"],
                    "name": f"{row['player__first_name']} {row['player__last_name']}".strip(),
                    "nickname": row["player__first_name"] or "",
                    "club": row.get("club_name") or "",
                    "club_logo": (cls._get_usage_url(owner_type=OwnerType.CLUB, owner_id=club_id) if club_id else None),
                    "avatar": row.get("player__avatar") or None,
                    "goals": int(row["goals"] or 0),
                }
            )
        return scorers

    @classmethod
    def _build_goals_evolution(cls, competitions, events):
        competition_goal_totals = (
            competitions.annotate(
                total_goals=Count(
                    "matches__events",
                    filter=Q(matches__events__event_type__in=cls.GOAL_EVENT_TYPES),
                )
            )
            .filter(total_goals__gt=0)
            .order_by("-total_goals", "-created_at")[:3]
        )

        evolution = []
        for competition in competition_goal_totals:
            periods = list(
                events.filter(
                    match__competition=competition,
                    event_type__in=cls.GOAL_EVENT_TYPES,
                )
                .annotate(period=TruncMonth("match__match_date"))
                .values("period")
                .annotate(goals=Count("id"))
                .order_by("period")
            )[-4:]

            evolution.append(
                {
                    "tournament_name": competition.name,
                    "data": [
                        {
                            "period": cls.MONTH_LABELS.get(item["period"].month, ""),
                            "goals": item["goals"],
                        }
                        for item in periods
                        if item["period"] is not None
                    ],
                }
            )

        return evolution

    @classmethod
    def _build_matches(cls, matches):
        return [
            {
                "id": match.id,
                "tournament": match.competition.name,
                "status": match.status,
                "date": match.match_date,
                "home_name": match.home_club.name,
                "home_logo": cls._get_usage_url(
                    owner_type=OwnerType.CLUB,
                    owner_id=match.home_club_id,
                ),
                "home_score": match.home_score,
                "away_name": match.away_club.name,
                "away_logo": cls._get_usage_url(
                    owner_type=OwnerType.CLUB,
                    owner_id=match.away_club_id,
                ),
                "away_score": match.away_score,
            }
            for match in matches.select_related("competition", "home_club", "away_club")
        ]

    @staticmethod
    def _get_usage_url(*, owner_type: str, owner_id):
        if not owner_id:
            return None
        return MediaAssetService.get_usage_url(
            owner_type=owner_type,
            owner_id=owner_id,
            role=AssetCategory.LOGO,
        )

    @staticmethod
    def _build_acronym(name: str) -> str:
        words = [word[0] for word in name.split() if word]
        if len(words) >= 2:
            return "".join(words[:3]).upper()
        return name[:3].upper()
