from datetime import date, timedelta

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
    PERIOD_DAY_MAP = {
        "7d": 7,
        "30d": 30,
        "90d": 90,
        "365d": 365,
    }
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
    def get_overview(
        cls,
        *,
        tenant=None,
        competition=None,
        club=None,
        period: str = "all",
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict:
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

        competitions, clubs, matches, events, registrations = cls._apply_entity_filters(
            competitions=competitions,
            clubs=clubs,
            matches=matches,
            events=events,
            registrations=registrations,
            competition=competition,
            club=club,
        )

        range_start, range_end = cls._resolve_date_range(
            period=period,
            start_date=start_date,
            end_date=end_date,
            competition=competition,
        )

        filtered_matches = cls._apply_match_date_filter(matches, range_start, range_end)
        filtered_events = cls._apply_event_date_filter(events, range_start, range_end)
        filtered_registrations = cls._apply_registration_date_filter(registrations, range_start, range_end)
        filtered_competitions = cls._apply_competition_period_filter(
            competitions=competitions,
            range_start=range_start,
            range_end=range_end,
            keep_all=competition is not None,
        )

        total_players = cls._count_distinct_players(filtered_registrations)
        if tenant is None and competition is None and club is None and total_players == 0:
            total_players = Player.objects.filter(status=Player.PlayerStatus.ACTIVE).count()

        total_tournaments = filtered_competitions.count()
        matches_finished = filtered_matches.filter(status=Match.MatchStatus.FINISHED).count()
        goals_total = filtered_events.filter(event_type__in=cls.GOAL_EVENT_TYPES).count()
        subscribers_count = subscriptions.count()
        today = timezone.localdate()

        players_this_month = filtered_registrations.filter(
            joined_date__year=today.year,
            joined_date__month=today.month,
        ).count()

        previous_month_date = today.replace(day=1) - timedelta(days=1)
        players_last_month = filtered_registrations.filter(
            joined_date__year=previous_month_date.year,
            joined_date__month=previous_month_date.month,
        ).count()

        avg_goals_per_match = round(goals_total / matches_finished, 2) if matches_finished else 0.0
        avg_subscribers_per_tournament = round(subscribers_count / total_tournaments, 2) if total_tournaments else 0.0

        return {
            "kpis": {
                "total_clubs": clubs.distinct().count(),
                "total_players": total_players,
                "total_news": 0,
                "active_tournaments": filtered_competitions.filter(status=CompetitionStatus.ACTIVE).count(),
                "tournaments_upcoming": filtered_competitions.filter(status=CompetitionStatus.DRAFT).count(),
                "tournaments_completed": filtered_competitions.filter(status=CompetitionStatus.COMPLETED).count(),
                "matches_finished": matches_finished,
                "matches_scheduled": filtered_matches.filter(status=Match.MatchStatus.SCHEDULED).count(),
                "matches_live": filtered_matches.filter(status=Match.MatchStatus.LIVE).count(),
                "total_matches": filtered_matches.count(),
                "matches_today": filtered_matches.filter(match_date__date=today).count(),
                "players_this_month": players_this_month,
                "players_last_month": players_last_month,
                "goals_total": goals_total,
                "avg_goals_per_match": avg_goals_per_match,
                "organization_subscribers": subscribers_count,
                "total_revenue": 0,
                "avg_subscribers_per_tournament": avg_subscribers_per_tournament,
            },
            "tournaments": cls._build_tournament_summaries(filtered_competitions),
            "top_clubs_by_players": cls._build_top_clubs(clubs=clubs, registrations=filtered_registrations),
            "top_scorers": cls._build_top_scorers(filtered_registrations),
            "goals_evolution": cls._build_goals_evolution(filtered_competitions, filtered_events),
            "live_matches": cls._build_matches(filtered_matches.filter(status=Match.MatchStatus.LIVE)[:5]),
            "upcoming_matches": cls._build_matches(
                filtered_matches.filter(status=Match.MatchStatus.SCHEDULED).order_by("match_date")[:5]
            ),
        }

    @classmethod
    def _apply_entity_filters(
        cls,
        *,
        competitions,
        clubs,
        matches,
        events,
        registrations,
        competition=None,
        club=None,
    ):
        if competition is not None:
            competitions = competitions.filter(id=competition.id)
            matches = matches.filter(competition=competition)
            events = events.filter(match__competition=competition)
            registrations = registrations.filter(competition=competition)
            clubs = clubs.filter(
                Q(competition_registrations__competition=competition)
                | Q(player_registrations__competition=competition)
                | Q(home_matches__competition=competition)
                | Q(away_matches__competition=competition)
            )

        if club is not None:
            clubs = clubs.filter(id=club.id)
            matches = matches.filter(Q(home_club=club) | Q(away_club=club))
            events = events.filter(club=club)
            registrations = registrations.filter(club=club)
            competitions = competitions.filter(
                Q(registrations__club=club)
                | Q(player_registrations__club=club)
                | Q(matches__home_club=club)
                | Q(matches__away_club=club)
            )

        return (
            competitions.distinct(),
            clubs.distinct(),
            matches.distinct(),
            events.distinct(),
            registrations.distinct(),
        )

    @classmethod
    def _resolve_date_range(
        cls,
        *,
        period: str,
        start_date: date | None,
        end_date: date | None,
        competition=None,
    ) -> tuple[date | None, date | None]:
        if start_date or end_date:
            return start_date, end_date

        if not period or period == "all":
            return None, None

        today = timezone.localdate()
        if period in cls.PERIOD_DAY_MAP:
            days = cls.PERIOD_DAY_MAP[period]
            return today - timedelta(days=days), today

        if period == "season":
            if competition is not None:
                return cls._season_bounds_from_value(competition.season)
            return cls._current_season_bounds(today)

        return None, None

    @staticmethod
    def _current_season_bounds(today: date) -> tuple[date, date]:
        start_year = today.year if today.month >= 7 else today.year - 1
        return date(start_year, 7, 1), date(start_year + 1, 6, 30)

    @staticmethod
    def _season_bounds_from_value(season: str) -> tuple[date, date]:
        if "/" in season:
            start_text, end_text = season.split("/", 1)
            start_year = int(start_text)
            end_suffix = int(end_text)
            end_year = (start_year // 100) * 100 + end_suffix
            if end_year < start_year:
                end_year += 100
            return date(start_year, 7, 1), date(end_year, 6, 30)

        year = int(season)
        return date(year, 1, 1), date(year, 12, 31)

    @staticmethod
    def _apply_match_date_filter(queryset, range_start: date | None, range_end: date | None):
        if range_start:
            queryset = queryset.filter(match_date__date__gte=range_start)
        if range_end:
            queryset = queryset.filter(match_date__date__lte=range_end)
        return queryset

    @staticmethod
    def _apply_event_date_filter(queryset, range_start: date | None, range_end: date | None):
        if range_start:
            queryset = queryset.filter(match__match_date__date__gte=range_start)
        if range_end:
            queryset = queryset.filter(match__match_date__date__lte=range_end)
        return queryset

    @staticmethod
    def _apply_registration_date_filter(queryset, range_start: date | None, range_end: date | None):
        if range_start:
            queryset = queryset.filter(joined_date__gte=range_start)
        if range_end:
            queryset = queryset.filter(joined_date__lte=range_end)
        return queryset

    @staticmethod
    def _apply_competition_period_filter(
        *, competitions, range_start: date | None, range_end: date | None, keep_all: bool
    ):
        if keep_all or (range_start is None and range_end is None):
            return competitions.distinct()

        match_filter = Q()
        registration_filter = Q()
        created_filter = Q()

        if range_start:
            match_filter &= Q(matches__match_date__date__gte=range_start)
            registration_filter &= Q(player_registrations__joined_date__gte=range_start)
            created_filter &= Q(created_at__date__gte=range_start)
        if range_end:
            match_filter &= Q(matches__match_date__date__lte=range_end)
            registration_filter &= Q(player_registrations__joined_date__lte=range_end)
            created_filter &= Q(created_at__date__lte=range_end)

        return competitions.filter(match_filter | registration_filter | created_filter).distinct()

    @staticmethod
    def _count_distinct_players(registrations) -> int:
        return registrations.values("player_id").distinct().count()

    @classmethod
    def _build_tournament_summaries(cls, competitions):
        queryset = (
            competitions.distinct()
            .annotate(
                teams_count=Count("registrations__club", distinct=True),
                matches_count=Count("matches", distinct=True),
                finished_matches_count=Count(
                    "matches",
                    filter=Q(matches__status=Match.MatchStatus.FINISHED),
                    distinct=True,
                ),
            )
            .order_by("-created_at")[:5]
        )

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
    def _build_top_clubs(cls, *, clubs, registrations):
        scoped_clubs = (
            clubs.filter(player_registrations__in=registrations).distinct() if registrations.exists() else clubs.none()
        )
        queryset = scoped_clubs.annotate(
            players_count=Count(
                "player_registrations__player",
                filter=Q(player_registrations__in=registrations),
                distinct=True,
            ),
            goals_total=Coalesce(
                Sum("player_registrations__goals", filter=Q(player_registrations__in=registrations)),
                0,
            ),
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
