from collections import defaultdict

from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, serializers
from drf_spectacular.utils import extend_schema, inline_serializer

from classificacoes.models import Standing
from matchengine.models import MatchEvent, MatchStats
from torneios.models import Tournament
from partidas.models import Match


FanPortalOrganizationSerializer = inline_serializer(
    name="FanPortalOrganization",
    fields={
        "id": serializers.CharField(),
        "name": serializers.CharField(),
        "slug": serializers.CharField(),
        "type": serializers.CharField(),
    },
)


FanPortalMatchEventSerializer = inline_serializer(
    name="FanPortalMatchEvent",
    fields={
        "id": serializers.CharField(),
        "type": serializers.CharField(),
        "minute": serializers.IntegerField(),
        "teamId": serializers.CharField(),
        "playerId": serializers.CharField(allow_null=True, required=False),
        "playerName": serializers.CharField(allow_null=True, required=False),
        "secondaryPlayerId": serializers.CharField(allow_null=True, required=False),
        "secondaryPlayerName": serializers.CharField(allow_null=True, required=False),
        "isOwnGoal": serializers.BooleanField(required=False),
        "playerAvatarUrl": serializers.CharField(allow_null=True, required=False),
    },
)


FanPortalMatchStatsSerializer = inline_serializer(
    name="FanPortalMatchStats",
    fields={
        "homePossession": serializers.IntegerField(),
        "awayPossession": serializers.IntegerField(),
        "homeShots": serializers.IntegerField(),
        "awayShots": serializers.IntegerField(),
        "homeCorners": serializers.IntegerField(),
        "awayCorners": serializers.IntegerField(),
        "homeFouls": serializers.IntegerField(),
        "awayFouls": serializers.IntegerField(),
    },
)


FanPortalTournamentSerializer = inline_serializer(
    name="FanPortalTournament",
    fields={
        "id": serializers.CharField(),
        "name": serializers.CharField(),
        "season": serializers.CharField(),
        "format": serializers.CharField(),
        "status": serializers.CharField(),
        "teamsCount": serializers.IntegerField(),
        "maxTeams": serializers.IntegerField(allow_null=True),
        "startDate": serializers.DateField(),
        "endDate": serializers.DateField(allow_null=True),
        "logoUrl": serializers.CharField(allow_null=True),
        "organization": FanPortalOrganizationSerializer,
        "table": serializers.ListField(child=serializers.DictField(), required=False),
        "groups": serializers.ListField(child=serializers.DictField(), required=False),
    },
)


FanPortalMatchSerializer = inline_serializer(
    name="FanPortalMatch",
    fields={
        "id": serializers.CharField(),
        "tournament": serializers.CharField(),
        "homeTeamId": serializers.CharField(),
        "homeTeamName": serializers.CharField(),
        "homeTeamLogoUrl": serializers.CharField(allow_null=True),
        "homeScore": serializers.IntegerField(allow_null=True),
        "awayTeamId": serializers.CharField(),
        "awayTeamName": serializers.CharField(),
        "awayTeamLogoUrl": serializers.CharField(allow_null=True),
        "awayScore": serializers.IntegerField(allow_null=True),
        "date": serializers.DateTimeField(),
        "time": serializers.CharField(),
        "status": serializers.CharField(),
        "round": serializers.CharField(),
        "stadium": serializers.CharField(),
        "events": serializers.ListField(child=FanPortalMatchEventSerializer, required=False),
        "stats": FanPortalMatchStatsSerializer,
    },
)


FanPortalParticipantSerializer = inline_serializer(
    name="FanPortalParticipant",
    fields={
        "id": serializers.CharField(),
        "name": serializers.CharField(),
        "avatar": serializers.CharField(allow_null=True, required=False),
        "acronym": serializers.CharField(allow_null=True, required=False),
        "shortName": serializers.CharField(allow_null=True, required=False),
    },
)


FanPortalTournamentOverviewSerializer = inline_serializer(
    name="FanPortalTournamentOverview",
    fields={
        "tournament": FanPortalTournamentSerializer,
        "matches": serializers.ListField(child=FanPortalMatchSerializer),
        "participants": serializers.ListField(child=FanPortalParticipantSerializer),
        "isSubscribed": serializers.BooleanField(),
    },
)


FanPortalSubscriptionSerializer = inline_serializer(
    name="FanPortalSubscription",
    fields={
        "subscribed": serializers.BooleanField(),
        "organization_id": serializers.CharField(),
        "organization_slug": serializers.CharField(),
        "tournament_id": serializers.CharField(),
    },
)


FanPortalSubscriptionOrganizationSerializer = inline_serializer(
    name="FanPortalSubscriptionOrganization",
    fields={
        "id": serializers.CharField(),
        "name": serializers.CharField(),
        "slug": serializers.CharField(),
        "type": serializers.CharField(),
        "country": serializers.CharField(),
        "location": serializers.CharField(),
    },
)


FanPortalProfileSerializer = inline_serializer(
    name="FanPortalProfile",
    fields={
        "id": serializers.CharField(),
        "name": serializers.CharField(),
        "email": serializers.CharField(),
        "subscriptions": serializers.ListField(child=FanPortalSubscriptionOrganizationSerializer),
        "subscriptionsCount": serializers.IntegerField(),
        "page": serializers.IntegerField(),
        "pageSize": serializers.IntegerField(),
    },
)


class FanPortalTournamentOverviewView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(responses=FanPortalTournamentOverviewSerializer)
    def get(self, request, tournament_id):
        tournament = get_object_or_404(
            Tournament.objects.select_related("tenant").prefetch_related("clubs"),
            id=tournament_id,
        )

        matches_qs = (
            Match.objects.filter(tournament=tournament)
            .select_related("home_team", "away_team", "venue")
            .order_by("date")
        )

        match_ids = list(matches_qs.values_list("id", flat=True))

        events_by_match = defaultdict(list)
        if match_ids:
            events_qs = (
                MatchEvent.objects.filter(match_id__in=match_ids)
                .select_related("team", "player")
                .order_by("minute", "created_at")
            )
            for e in events_qs:
                player = e.player
                player_avatar_url = None
                if player and getattr(player, "avatar", None):
                    url = player.avatar.url
                    player_avatar_url = (
                        request.build_absolute_uri(url) if request else url
                    )
                events_by_match[e.match_id].append(
                    {
                        "id": str(e.id),
                        "type": e.type,
                        "minute": e.minute,
                        "teamId": str(e.team_id),
                        "playerId": str(e.player_id) if e.player_id else None,
                        "playerName": player.name if player else None,
                        "secondaryPlayerId": (
                            str(e.secondary_player_id) if e.secondary_player_id else None
                        ),
                        "secondaryPlayerName": (
                            e.secondary_player.name if e.secondary_player else None
                        ),
                        "isOwnGoal": e.is_own_goal,
                        "playerAvatarUrl": player_avatar_url,
                    }
                )

        stats_by_match = {}
        if match_ids:
            stats_qs = MatchStats.objects.filter(match_id__in=match_ids)
            for s in stats_qs:
                stats_by_match[s.match_id] = {
                    "homePossession": s.home_possession,
                    "awayPossession": s.away_possession,
                    "homeShots": s.home_shots,
                    "awayShots": s.away_shots,
                    "homeCorners": s.home_corners,
                    "awayCorners": s.away_corners,
                    "homeFouls": s.home_fouls,
                    "awayFouls": s.away_fouls,
                }

        team_results = defaultdict(list)
        for m in matches_qs:
            if m.status != "finished":
                continue
            if m.home_score is None or m.away_score is None:
                continue
            home_id = str(m.home_team_id) if m.home_team_id else None
            away_id = str(m.away_team_id) if m.away_team_id else None
            if not home_id or not away_id:
                continue
            if m.home_score > m.away_score:
                team_results[home_id].append("W")
                team_results[away_id].append("L")
            elif m.home_score < m.away_score:
                team_results[home_id].append("L")
                team_results[away_id].append("W")
            else:
                team_results[home_id].append("D")
                team_results[away_id].append("D")

        def build_logo_url(club):
            if not club:
                return None
            logo = getattr(club, "logo", None)
            if not logo or not getattr(logo, "name", None):
                return None
            try:
                storage = logo.storage
                if not storage.exists(logo.name):
                    return None
                url = logo.url
            except Exception:
                return None
            return request.build_absolute_uri(url) if request else url

        matches = []
        for m in matches_qs:
            match_events = events_by_match.get(m.id) or []

            home_score = m.home_score
            away_score = m.away_score

            if match_events and (m.status == "live" or home_score is None or away_score is None):
                home_id = str(m.home_team_id) if m.home_team_id else None
                away_id = str(m.away_team_id) if m.away_team_id else None
                home_goals = 0
                away_goals = 0

                for e in match_events:
                    if e["type"] != "goal":
                        continue
                    team_id = e.get("teamId")
                    is_own_goal = e.get("isOwnGoal")
                    if is_own_goal:
                        if team_id == home_id:
                            away_goals += 1
                        elif team_id == away_id:
                            home_goals += 1
                    else:
                        if team_id == home_id:
                            home_goals += 1
                        elif team_id == away_id:
                            away_goals += 1

                if m.status == "live" or home_score is None or away_score is None:
                    home_score = home_goals
                    away_score = away_goals

            match_payload = {
                "id": str(m.id),
                "tournament": str(tournament.id),
                "homeTeamId": str(m.home_team_id) if m.home_team_id else "",
                "homeTeamName": m.home_team.name if m.home_team else "",
                "homeTeamLogoUrl": build_logo_url(m.home_team),
                "homeScore": home_score,
                "awayTeamId": str(m.away_team_id) if m.away_team_id else "",
                "awayTeamName": m.away_team.name if m.away_team else "",
                "awayTeamLogoUrl": build_logo_url(m.away_team),
                "awayScore": away_score,
                "date": m.date,
                "time": m.date.strftime("%H:%M"),
                "status": m.status,
                "round": m.round or "",
                "stadium": m.venue.name if m.venue else "",
            }
            if match_events:
                match_payload["events"] = match_events
            match_stats = stats_by_match.get(m.id)
            if match_stats:
                match_payload["stats"] = match_stats
            matches.append(match_payload)

        participants = []
        for club in tournament.clubs.all().order_by("name"):
            participants.append(
                {
                    "id": str(club.id),
                    "name": club.name,
                    "avatar": build_logo_url(club),
                    "acronym": club.acronym,
                    "shortName": club.short_name,
                }
            )

        user = request.user if request.user.is_authenticated else None
        is_subscribed = False
        if user and hasattr(user, "subscriptions"):
            is_subscribed = user.subscriptions.filter(id=tournament.tenant_id).exists()

        tenant = tournament.tenant
        org_data = {
            "id": str(tenant.id),
            "name": tenant.name,
            "slug": tenant.slug,
            "type": tenant.type,
        }

        tournament_type = (tournament.type or "").lower()
        if tournament_type.startswith("league"):
            format_value = "league"
        elif tournament_type.startswith("knockout"):
            format_value = "knockout"
        elif tournament_type.startswith("groups"):
            format_value = "groups"
        else:
            format_value = "league"

        standings_qs = (
            Standing.objects.filter(tenant=tournament.tenant, tournament=tournament)
            .select_related("club", "group")
            .order_by("-points", "-goals_for")
        )

        table = []
        groups_map = defaultdict(list)
        for s in standings_qs:
            club_id = str(s.club_id)
            form = team_results.get(club_id, [])
            entry = {
                "teamId": club_id,
                "teamName": s.club.name if s.club else "",
                "played": s.played,
                "won": s.wins,
                "drawn": s.draws,
                "lost": s.losses,
                "goalsFor": s.goals_for,
                "goalsAgainst": s.goals_against,
                "goalDifference": s.goals_for - s.goals_against,
                "points": s.points,
                "form": form[-5:],
            }
            if s.group_id:
                groups_map[s.group_id].append(entry)
            else:
                table.append(entry)

        groups_payload = []
        if groups_map:
            group_ids = list(groups_map.keys())
            from torneios.models import TournamentGroup

            group_objs = {
                g.id: g
                for g in TournamentGroup.objects.filter(
                    id__in=group_ids, tournament=tournament
                )
            }
            for group_id, entries in groups_map.items():
                group_obj = group_objs.get(group_id)
                groups_payload.append(
                    {
                        "id": str(group_id),
                        "name": group_obj.name if group_obj else "",
                        "table": entries,
                        "matches": [],
                        "participantIds": [e["teamId"] for e in entries],
                    }
                )

        tournament_data = {
            "id": str(tournament.id),
            "name": tournament.name,
            "season": tournament.season,
            "format": format_value,
            "status": tournament.status,
            "teamsCount": tournament.clubs.count(),
            "maxTeams": tournament.max_teams,
            "startDate": tournament.start_date,
            "endDate": tournament.end_date,
            "logoUrl": request.build_absolute_uri(tournament.logo.url)
            if tournament.logo and request
            else None,
            "organization": org_data,
            "table": table,
            "groups": groups_payload,
        }

        data = {
            "tournament": tournament_data,
            "matches": matches,
            "participants": participants,
            "isSubscribed": is_subscribed,
        }

        return Response(data)


class FanPortalTournamentSubscribeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses=FanPortalSubscriptionSerializer)
    def post(self, request, tournament_id):
        tournament = get_object_or_404(
            Tournament.objects.select_related("tenant"),
            id=tournament_id,
        )
        tenant = tournament.tenant
        user = request.user
        user.subscriptions.add(tenant)
        data = {
            "subscribed": True,
            "organization_id": str(tenant.id),
            "organization_slug": tenant.slug,
            "tournament_id": str(tournament.id),
        }
        return Response(data)


class FanPortalTournamentUnsubscribeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses=FanPortalSubscriptionSerializer)
    def post(self, request, tournament_id):
        tournament = get_object_or_404(
            Tournament.objects.select_related("tenant"),
            id=tournament_id,
        )
        tenant = tournament.tenant
        user = request.user
        user.subscriptions.remove(tenant)
        data = {
            "subscribed": False,
            "organization_id": str(tenant.id),
            "organization_slug": tenant.slug,
            "tournament_id": str(tournament.id),
        }
        return Response(data)


class FanPortalProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses=FanPortalProfileSerializer)
    def get(self, request):
        user = request.user
        page_param = request.query_params.get("page") or "1"
        page_size_param = request.query_params.get("page_size") or "8"
        search = request.query_params.get("search") or ""
        org_type = request.query_params.get("type") or ""

        try:
            page = int(page_param)
        except (TypeError, ValueError):
            page = 1
        if page < 1:
            page = 1

        try:
            page_size = int(page_size_param)
        except (TypeError, ValueError):
            page_size = 8
        if page_size < 1:
            page_size = 8
        if page_size > 50:
            page_size = 50

        subscriptions_qs = getattr(user, "subscriptions", None)
        organizations = []
        total_count = 0
        if subscriptions_qs is not None:
            qs = subscriptions_qs.all().order_by("name")

            if search:
                qs = qs.filter(name__icontains=search)

            if org_type:
                qs = qs.filter(type=org_type)

            total_count = qs.count()

            start = (page - 1) * page_size
            end = start + page_size
            qs_page = qs[start:end]

            for tenant in qs_page:
                organizations.append(
                    {
                        "id": str(tenant.id),
                        "name": tenant.name,
                        "slug": tenant.slug,
                        "type": tenant.type,
                        "country": tenant.country,
                        "location": tenant.location,
                    }
                )

        data = {
            "id": str(user.id),
            "name": user.name or user.username,
            "email": user.email,
            "subscriptions": organizations,
            "subscriptionsCount": total_count,
            "page": page,
            "pageSize": page_size,
        }
        return Response(data)
