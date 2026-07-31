"""
BOLAYETU — Lineup & Match Report Viewsets

REST API endpoints for matches, lineups, and match reports.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from common.pagination import StandardPagination
from competitions.models import Match, MatchLineup, LineupSubmission, MatchReport, Goal, MatchStats
from competitions.serializers import (
    LineupSubmissionSerializer, LineupSubmissionInputSerializer,
    LineupSubmissionDetailSerializer, MatchLineupPlayerSerializer,
    MatchReportSerializer, MatchReportInputSerializer,
    GoalInputSerializer, GoalSerializer
)
from competitions.services.lineup_service import (
    LineupService, LineupValidationError, PlayerNotEligible,
    LineupAlreadySubmitted
)
from clubs.models import Club
from players.models import Player


# ─── Tenant Helper ────────────────────────────────────────────────────────────

def get_request_tenant(request):
    """
    Resolve o tenant a partir do request de forma robusta.

    Estratégia (por prioridade):
      1. request.tenant  — injetado pelo TenantMiddleware (subdomain)
      2. Header X-Tenant-ID — útil para clientes API que passam o UUID do tenant
      3. TenantMembership  — primeira membership ativa do utilizador autenticado

    Retorna None se nenhuma estratégia tiver sucesso.
    """
    # 1. Middleware (subdomain resolve)
    tenant = getattr(request, "tenant", None)
    if tenant is not None:
        return tenant

    # 2. Header explícito (X-Tenant-ID: <uuid>)
    tenant_id = request.headers.get("X-Tenant-ID") or request.META.get("HTTP_X_TENANT_ID")
    if tenant_id:
        from core.models import Tenant
        try:
            return Tenant.objects.get(id=tenant_id)
        except (Tenant.DoesNotExist, Exception):
            pass

    # 3. Primeira membership ativa do utilizador
    if request.user and request.user.is_authenticated:
        from accounts.models import TenantMembership
        membership = (
            TenantMembership.objects
            .filter(user=request.user, is_active=True)
            .select_related("tenant")
            .first()
        )
        if membership:
            return membership.tenant

    return None


# ─── Lineup Submission Viewset ─────────────────────────────────────────────


class LineupSubmissionViewSet(viewsets.ModelViewSet):
    """
    API endpoints for match lineup management.

    - POST /competitions/matches/{match_id}/lineups/
        Submit lineup for a club
    - GET /competitions/matches/{match_id}/lineups/
        Get all lineups for a match
    - GET /competitions/matches/{match_id}/lineups/{club_id}/
        Get lineup for specific club
    - POST /competitions/matches/{match_id}/lineups/{club_id}/confirm/
        Confirm a submitted lineup
    - POST /competitions/matches/{match_id}/lineups/{club_id}/lock/
        Lock a lineup (no further changes)
    """

    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination

    def get_queryset(self):
        """Filter lineups by tenant and match."""
        tenant = get_request_tenant(self.request)
        match_id = self.kwargs.get('match_id')

        qs = LineupSubmission.objects.select_related('match', 'club', 'submitted_by')

        if tenant:
            qs = qs.filter(tenant=tenant, match_id=match_id)
        else:
            qs = qs.filter(match_id=match_id)

        return qs

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return LineupSubmissionInputSerializer
        elif self.action == 'retrieve':
            return LineupSubmissionDetailSerializer
        return LineupSubmissionSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Submit a lineup for a club in a match.

        Expected request body:
        {
            "club_id": "uuid",          ← optional if only one club per user
            "formation": "4-3-3",
            "players": [
                {
                    "player_id": "uuid",
                    "status": "starter",
                    "position": "gk",
                    "shirt_number": 1,
                    "is_captain": false,
                    "is_goalkeeper": true,
                    "formation_position": 1
                },
                ...
            ]
        }
        """
        tenant = get_request_tenant(request)
        if tenant is None:
            return Response(
                {"error": "Tenant não identificado. Verifica o cabeçalho X-Tenant-ID ou o subdomínio."},
                status=status.HTTP_400_BAD_REQUEST
            )

        match_id = self.kwargs.get('match_id')

        # Get match
        match = get_object_or_404(Match, id=match_id, tenant=tenant)

        # Get club_id from request body or from user's club context
        club_id = request.data.get('club_id')
        if not club_id:
            return Response(
                {"error": "club_id é obrigatório no corpo do pedido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        club = get_object_or_404(Club, id=club_id, tenant=tenant)

        # Validate input
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            # Submit lineup using service
            submission = LineupService.submit_lineup(
                tenant=tenant,
                match=match,
                club=club,
                players=serializer.validated_data['players'],
                formation=serializer.validated_data.get('formation', ''),
                submitted_by=request.user
            )

            # Return created lineup
            response_serializer = LineupSubmissionDetailSerializer(submission)
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )

        except LineupAlreadySubmitted:
            return Response(
                {"error": "A escalação está bloqueada e não pode ser alterada."},
                status=status.HTTP_400_BAD_REQUEST
            )
        except LineupValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except PlayerNotEligible as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def retrieve(self, request, *args, **kwargs):
        """Get lineup for a specific club in a match."""
        tenant = get_request_tenant(request)
        match_id = self.kwargs.get('match_id')
        club_id = self.kwargs.get('pk')  # club_id in URL

        qs = LineupSubmission.objects.filter(match_id=match_id, club_id=club_id)
        if tenant:
            qs = qs.filter(tenant=tenant)

        try:
            submission = qs.get()
        except LineupSubmission.DoesNotExist:
            return Response(
                {"error": "Escalação não encontrada"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(submission)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        """Get all lineups for a match."""
        tenant = get_request_tenant(request)
        match_id = self.kwargs.get('match_id')

        match_qs = Match.objects.filter(id=match_id)
        if tenant:
            match_qs = match_qs.filter(tenant=tenant)

        try:
            match = match_qs.get()
        except Match.DoesNotExist:
            return Response(
                {"error": "Jogo não encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )

        lineups_qs = LineupSubmission.objects.filter(match=match).select_related('club', 'match')
        if tenant:
            lineups_qs = lineups_qs.filter(tenant=tenant)

        serializer = self.get_serializer(lineups_qs, many=True)
        return Response({
            "match_id": str(match.id),
            "match_str": str(match),
            "lineups": serializer.data
        })

    @action(detail=False, methods=['post'])
    @transaction.atomic
    def confirm(self, request, *args, **kwargs):
        """Confirm a submitted lineup."""
        tenant = get_request_tenant(request)
        if tenant is None:
            return Response(
                {"error": "Tenant não identificado."},
                status=status.HTTP_400_BAD_REQUEST
            )

        match_id = self.kwargs.get('match_id')
        club_id = request.data.get('club_id')

        if not club_id:
            return Response(
                {"error": "club_id é obrigatório"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            match = Match.objects.get(id=match_id, tenant=tenant)
            club = Club.objects.get(id=club_id, tenant=tenant)

            submission = LineupService.confirm_lineup(
                tenant=tenant,
                match=match,
                club=club,
                confirmed_by=request.user
            )

            serializer = LineupSubmissionDetailSerializer(submission)
            return Response(serializer.data)

        except Match.DoesNotExist:
            return Response(
                {"error": "Jogo não encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Club.DoesNotExist:
            return Response(
                {"error": "Clube não encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )
        except LineupValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'])
    @transaction.atomic
    def lock(self, request, *args, **kwargs):
        """Lock all lineups for a match."""
        tenant = get_request_tenant(request)
        if tenant is None:
            return Response(
                {"error": "Tenant não identificado."},
                status=status.HTTP_400_BAD_REQUEST
            )

        match_id = self.kwargs.get('match_id')

        try:
            match = Match.objects.get(id=match_id, tenant=tenant)

            LineupService.lock_all_lineups(
                tenant=tenant,
                match=match
            )

            submissions = LineupSubmission.objects.filter(tenant=tenant, match=match)
            serializer = self.get_serializer(submissions, many=True)
            return Response({
                "message": "Todas as escalações bloqueadas",
                "lineups": serializer.data
            })

        except Match.DoesNotExist:
            return Response(
                {"error": "Jogo não encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )


# ─── Match Report Viewset ──────────────────────────────────────────────────


class MatchReportViewSet(viewsets.ModelViewSet):
    """
    API endpoints for match reports and statistics.

    - GET /competitions/matches/{match_id}/report/
        Get match report (lineups, goals, stats)
    - POST /competitions/matches/{match_id}/report/create/
        Create/update match report
    - POST /competitions/matches/{match_id}/report/add-goal/
        Record a goal
    - POST /competitions/matches/{match_id}/report/update-stats/
        Update team statistics
    """

    permission_classes = [IsAuthenticated]
    serializer_class = MatchReportSerializer

    def get_queryset(self):
        """Filter reports by tenant and match."""
        tenant = get_request_tenant(self.request)
        match_id = self.kwargs.get('match_id')

        qs = MatchReport.objects.select_related('match').filter(match_id=match_id)
        if tenant:
            qs = qs.filter(match__tenant=tenant)
        return qs

    @action(detail=False, methods=['get'])
    def get_report(self, request, *args, **kwargs):
        """Get match report with lineups, goals, and statistics."""
        tenant = get_request_tenant(request)
        match_id = self.kwargs.get('match_id')

        match_qs = Match.objects.filter(id=match_id)
        if tenant:
            match_qs = match_qs.filter(tenant=tenant)

        try:
            match = match_qs.get()

            # Get or create report
            report, _ = MatchReport.objects.get_or_create(match=match)

            # Get lineups
            lineups_qs = LineupSubmission.objects.filter(match=match).select_related('club')
            if tenant:
                lineups_qs = lineups_qs.filter(tenant=tenant)

            serializer = self.get_serializer(report)

            return Response({
                "match": {
                    "id": str(match.id),
                    "home_club": match.home_club.name,
                    "away_club": match.away_club.name,
                    "scheduled_for": match.scheduled_for,
                },
                "report": serializer.data,
                "lineups": LineupSubmissionDetailSerializer(lineups_qs, many=True).data
            })

        except Match.DoesNotExist:
            return Response(
                {"error": "Jogo não encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['post'])
    @transaction.atomic
    def create_report(self, request, *args, **kwargs):
        """Create or update match report."""
        tenant = get_request_tenant(request)
        match_id = self.kwargs.get('match_id')

        match_qs = Match.objects.filter(id=match_id)
        if tenant:
            match_qs = match_qs.filter(tenant=tenant)

        try:
            match = match_qs.get()

            serializer = MatchReportInputSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            report, created = MatchReport.objects.get_or_create(match=match)

            report.home_score = serializer.validated_data['home_score']
            report.away_score = serializer.validated_data['away_score']

            if 'match_duration' in serializer.validated_data:
                report.match_duration = serializer.validated_data['match_duration']

            report.save()

            response_serializer = self.get_serializer(report)
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
            )

        except Match.DoesNotExist:
            return Response(
                {"error": "Jogo não encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['post'])
    @transaction.atomic
    def add_goal(self, request, *args, **kwargs):
        """Record a goal in the match."""
        tenant = get_request_tenant(request)
        match_id = self.kwargs.get('match_id')

        serializer = GoalInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            match_qs = Match.objects.filter(id=match_id)
            if tenant:
                match_qs = match_qs.filter(tenant=tenant)
            match = match_qs.get()

            # Player is global — sem filtro de tenant
            try:
                player = Player.objects.get(id=serializer.validated_data['player_id'])
            except Player.DoesNotExist:
                return error_response(message="Player not found.", status_code=404)

            club_qs = Club.objects.filter(id=serializer.validated_data['club_id'])
            if tenant:
                club_qs = club_qs.filter(tenant=tenant)
            club = club_qs.get()

            # Get or create report
            report, _ = MatchReport.objects.get_or_create(match=match)

            # Create goal
            goal = Goal.objects.create(
                match=match,
                player=player,
                club=club,
                minute=serializer.validated_data['minute'],
                goal_type=serializer.validated_data['goal_type'],
            )

            if 'assist_player_id' in serializer.validated_data:
                try:
                    assist_player = Player.objects.get(
                        id=serializer.validated_data['assist_player_id']
                    )
                    goal.assist_player = assist_player
                    goal.save()
                except Player.DoesNotExist:
                    pass

            response_serializer = GoalSerializer(goal)
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )

        except (Match.DoesNotExist, Player.DoesNotExist, Club.DoesNotExist):
            return Response(
                {"error": "Jogo, jogador ou clube não encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['post'])
    @transaction.atomic
    def update_stats(self, request, *args, **kwargs):
        """Update team statistics for the match."""
        tenant = get_request_tenant(request)
        match_id = self.kwargs.get('match_id')

        club_id = request.data.get('club_id')
        if not club_id:
            return Response(
                {"error": "club_id é obrigatório"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            match_qs = Match.objects.filter(id=match_id)
            if tenant:
                match_qs = match_qs.filter(tenant=tenant)
            match = match_qs.get()

            club_qs = Club.objects.filter(id=club_id)
            if tenant:
                club_qs = club_qs.filter(tenant=tenant)
            club = club_qs.get()

            stats, created = MatchStats.objects.get_or_create(match=match, club=club)

            # Update fields from request
            for field in ['possession', 'shots_on_goal', 'shots_off_goal',
                         'passes', 'passes_accuracy', 'fouls',
                         'yellow_cards', 'red_cards', 'corner_kicks']:
                if field in request.data:
                    setattr(stats, field, request.data[field])

            stats.save()

            from competitions.serializers import MatchStatsSerializer
            serializer = MatchStatsSerializer(stats)
            return Response(serializer.data)

        except (Match.DoesNotExist, Club.DoesNotExist):
            return Response(
                {"error": "Jogo ou clube não encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )
