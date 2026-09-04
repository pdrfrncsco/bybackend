"""
BOLAYETU — Match Center Views (Phase 4)

Endpoints:
  GET  /api/v1/competitions/<competition_id>/matches/<match_id>/events/  → public súmula
  POST /api/v1/competitions/<competition_id>/matches/<match_id>/events/  → add event (admin)
  DELETE /api/v1/competitions/<competition_id>/matches/<match_id>/events/<event_id>/ → remove event (admin)
  GET  /api/v1/competitions/<competition_id>/stats/  → player stats leaderboard (public)
  GET  /api/v1/matches/live/  → live matches globally
"""

from django.db.models import Q
import json
import time
from django.http import StreamingHttpResponse
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_spectacular.utils import extend_schema
from rest_framework.parsers import MultiPartParser, FormParser

from accounts.permissions import IsActiveAccount
from clubs.models import Club
from players.models import Player
from competitions.models import Competition
from competitions.selectors import CompetitionSelector
from common.responses import (
    success_response, created_response, not_found_response, error_response
)
from common.renderers import ServerSentEventsRenderer
from organizations.permissions import IsOrganizationAdmin
from competitions.permissions import IsMatchEventOperator
from organizations.services import OrganizationService
from competitions.models import Match, MatchEvent
from competitions.serializers.v2_serializers import MatchSerializer
from competitions.services.match_event_service import (
    MatchEventService, MatchEventNotFound, InvalidMatchEventData
)
from competitions.serializers.match_event_serializers import (
    MatchEventSerializer, MatchEventCreateSerializer, PlayerStatsSerializer
)

User = get_user_model()


class MatchEventListCreateView(APIView):
    """
    GET  → public: list all events for a match (súmula).
    POST → org admin: add an in-game event.
    """

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated(), IsActiveAccount(), IsMatchEventOperator()]

    @extend_schema(
        tags=["match-center"],
        summary="List match events (súmula)",
        responses={200: MatchEventSerializer(many=True)},
    )
    def get(self, request, competition_id, match_id):
        competition = CompetitionSelector.get_by_id_public(competition_id=competition_id)
        if competition is None:
            return not_found_response(message="Competition not found.")
        try:
            match = Match.objects.select_related("tenant").get(id=match_id, competition_id=competition.id)
        except Match.DoesNotExist:
            return not_found_response(message="Match not found.")

        events = MatchEventService.list_events_for_match(
            tenant=match.tenant, match_id=match_id
        )
        return success_response(
            data=MatchEventSerializer(events, many=True).data,
            message="Match events retrieved successfully.",
        )

    @extend_schema(
        tags=["match-center"],
        summary="Add in-game event (admin)",
        request=MatchEventCreateSerializer,
        responses={201: MatchEventSerializer},
    )
    def post(self, request, competition_id, match_id):
        tenant = OrganizationService.get_organization_for_user(user=request.user)

        competition = CompetitionSelector.get_by_id_public(competition_id=competition_id)
        if competition is None:
            return not_found_response(message="Competition not found.")
        try:
            match = Match.objects.get(id=match_id, competition_id=competition.id, tenant=tenant)
        except Match.DoesNotExist:
            return not_found_response(message="Match not found.")

        serializer = MatchEventCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Resolve club
        try:
            club = Club.objects.get(id=data["club"], tenant=tenant)
        except Club.DoesNotExist:
            return not_found_response(message="Club not found.")

        # Resolve optional players
        player = None
        if data.get("player"):
            try:
                player = Player.objects.get(id=data["player"])
            except Player.DoesNotExist:
                return not_found_response(message="Player not found.")

        player_off = None
        if data.get("player_off"):
            try:
                player_off = Player.objects.get(id=data["player_off"])
            except Player.DoesNotExist:
                return not_found_response(message="Player (off) not found.")

        try:
            event = MatchEventService.add_event(
                tenant=tenant,
                match=match,
                club=club,
                event_type=data["event_type"],
                minute=data["minute"],
                player=player,
                player_off=player_off,
                extra_time=data.get("extra_time", False),
                notes=data.get("notes", ""),
                idempotency_key=data.get("idempotency_key"),
            )
        except InvalidMatchEventData as exc:
            return error_response(message=str(exc), status_code=400)

        return created_response(
            data=MatchEventSerializer(event).data,
            message="Event added successfully.",
        )


class MatchEventDeleteView(APIView):
    """
    DELETE → org admin: remove an event (and recalculate score if goal).
    """
    permission_classes = [IsAuthenticated, IsActiveAccount, IsOrganizationAdmin]

    @extend_schema(
        tags=["match-center"],
        summary="Remove match event (admin)",
        responses={200: None},
    )
    def delete(self, request, competition_id, match_id, event_id):
        tenant = OrganizationService.get_organization_for_user(user=request.user)
        try:
            MatchEventService.remove_event(tenant=tenant, event_id=event_id)
        except MatchEventNotFound:
            return not_found_response(message="Event not found.")
        return success_response(data=None, message="Event removed successfully.")


class CompetitionPlayerStatsView(APIView):
    """
    GET → public: player stats leaderboard for a competition by ID or slug.
    (goals, cards, appearances sorted by goals desc)
    """
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["match-center"],
        summary="Player stats leaderboard for competition",
        responses={200: PlayerStatsSerializer(many=True)},
    )
    def get(self, request, competition_id):
        competition = CompetitionSelector.get_by_id_public(competition_id=competition_id)
        if competition is None:
            return not_found_response(message="Competition not found.")

        stats = MatchEventService.get_player_stats_for_competition(
            tenant=competition.tenant,
            competition_id=competition.id,
        )
        return success_response(
            data=PlayerStatsSerializer(stats, many=True).data,
            message="Player stats retrieved successfully.",
        )


class LiveMatchesView(APIView):
    """
    GET → public: list all live matches globally.
    
    Returns matches with status='live' or status='halftime',
    with all related data (home/away clubs, competition).
    """
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["match-center"],
        summary="List live matches globally",
        responses={200: MatchSerializer(many=True)},
    )
    def get(self, request):
        matches = Match.objects.filter(
            status__in=['live', 'halftime']
        ).select_related(
            'home_club', 'away_club', 'competition'
        ).prefetch_related('events')
        
        serializer = MatchSerializer(matches, many=True)
        return success_response(
            data=serializer.data,
            message="Live matches retrieved successfully."
        )


class MatchStreamView(APIView):
    """Authenticated SSE stream for one match; HTTP polling remains the fallback."""

    permission_classes = []
    renderer_classes = [ServerSentEventsRenderer]
    POLL_INTERVAL = 2
    MAX_STREAM_DURATION = 20

    @staticmethod
    def _event(name, payload):
        return f"event: {name}\ndata: {json.dumps(payload, default=str)}\n\n"

    def _user_from_token(self, request):
        raw_token = request.GET.get("token")
        if not raw_token:
            return None
        try:
            validated = AccessToken(raw_token)
            return User.objects.get(pk=validated["user_id"])
        except (InvalidToken, TokenError, User.DoesNotExist):
            return None

    def get(self, request, match_id):
        user = self._user_from_token(request)
        if user is None:
            return StreamingHttpResponse(
                (self._event("error", {"detail": "Authentication required."}),),
                content_type="text/event-stream",
            )
        try:
            tenant = OrganizationService.get_organization_for_user(user=user)
            match = Match.objects.select_related("home_club", "away_club", "competition").get(
                id=match_id, tenant=tenant,
            )
        except (Match.DoesNotExist, Exception) as exc:
            if isinstance(exc, Match.DoesNotExist):
                return StreamingHttpResponse(
                    (self._event("error", {"detail": "Match not found."}),),
                    content_type="text/event-stream",
                )
            return StreamingHttpResponse(
                (self._event("error", {"detail": "Match access unavailable."}),),
                content_type="text/event-stream",
            )

        def stream():
            last_match_updated = None
            last_event_updated = None
            started_at = time.monotonic()
            yield self._event("snapshot", {"match": MatchSerializer(match).data})
            while True:
                remaining = self.MAX_STREAM_DURATION - (time.monotonic() - started_at)
                if remaining <= 0:
                    return

                time.sleep(min(self.POLL_INTERVAL, remaining))
                current = Match.objects.select_related("home_club", "away_club", "competition").get(id=match.id)
                current_updated = str(current.updated_at)
                if current_updated != last_match_updated:
                    yield self._event("match_state", {"match": MatchSerializer(current).data})
                    last_match_updated = current_updated
                events = MatchEvent.objects.filter(match_id=match.id).select_related("player", "player_off", "club").order_by("created_at")
                new_events = [event for event in events if last_event_updated is None or str(event.created_at) > last_event_updated]
                for event in new_events:
                    yield self._event("match_event", {"event": MatchEventSerializer(event).data})
                if new_events:
                    last_event_updated = str(new_events[-1].created_at)
                yield self._event("ping", {"ts": str(time.time())})

        response = StreamingHttpResponse(stream(), content_type="text/event-stream")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response


class MatchReportDocumentUploadView(APIView):
    """
    POST → referee/admin: upload referee report PDF document.
    
    Accepts multipart/form-data with a 'document' file field.
    Stores the document in DAM and returns the URL.
    """
    permission_classes = [IsAuthenticated, IsActiveAccount]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        tags=["match-center"],
        summary="Upload referee report document (PDF)",
        request=None,  # No schema for multipart/form-data
        responses={
            201: {
                "type": "object",
                "properties": {
                    "document_url": {"type": "string", "format": "uri"},
                }
            }
        },
    )
    def post(self, request, match_id):
        tenant = OrganizationService.get_organization_for_user(user=request.user)
        
        # Check file exists
        document = request.FILES.get('document')
        if not document:
            return error_response(message="No document file provided")

        # Validate PDF content type
        content_type = document.content_type
        if content_type != 'application/pdf' and not document.name.endswith('.pdf'):
            return error_response(message="Only PDF files are accepted", status_code=400)

        # Limit file size to 10MB
        if document.size > 10 * 1024 * 1024:
            return error_response(message="File size exceeds 10MB limit", status_code=400)

        # Verify match exists and belongs to tenant
        try:
            match = Match.objects.select_related('home_club', 'away_club').get(
                id=match_id,
                tenant=tenant
            )
        except Match.DoesNotExist:
            return not_found_response(message="Match not found")

        # Upload to DAM (Document Asset Management)
        from media_assets.models import MediaAsset
        from media_assets.services import DAMService
        
        try:
            # Create media asset
            asset = MediaAsset.objects.create(
                tenant=tenant,
                file=document,
                name=f"match_report_{match.id}_{document.name}",
                mime_type=document.content_type,
                uploaded_by=request.user,
            )
            
            return success_response(
                data={'document_url': asset.file.url},
                message="Document uploaded successfully.",
                status_code=201
            )
            
        except Exception as e:
            return error_response(
                message=f"Failed to upload document: {str(e)}",
                status_code=500
            )
