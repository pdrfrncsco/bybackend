"""
BOLAYETU — Player Views

API endpoints for players (public, global domain).

Public endpoints (no auth required):
    GET    /api/v1/players/              — List active players (filterable by position/nationality)
    GET    /api/v1/players/search/       — Search players by name
    GET    /api/v1/players/{slug}/       — Get player detail + career history

Staff-only write endpoints:
    POST   /api/v1/players/              — Create a new player
    PATCH  /api/v1/players/{slug}/       — Update player profile

Registration endpoints (requires tenant membership):
    POST   /api/v1/players/{slug}/register/     — Register player at a club
    PATCH  /api/v1/players/registrations/{id}/  — Update registration stats
"""

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from common.responses import success_response, error_response
from common.pagination import StandardPagination
from players.models import Player, PlayerRegistration
from players.selectors import PlayerSelector, PlayerRegistrationSelector
from players.serializers import PlayerSerializer, PlayerDetailSerializer, PlayerRegistrationSerializer
from players.services import PlayerService, PlayerRegistrationService, PlayerNotFound, PlayerRegistrationConflict
from players.permissions import IsStaffOrReadOnly, CanManagePlayerRegistrations


class PlayerListCreateView(APIView):
    """
    GET:  List all active players. Supports ?position= and ?nationality= filters.
    POST: Create a new player (staff only).
    """

    permission_classes = [IsStaffOrReadOnly]

    @extend_schema(
        tags=["players"],
        summary="List players",
        parameters=[
            OpenApiParameter("position", OpenApiTypes.STR, description="Filter by position code (gk, cb, st, ...)"),
            OpenApiParameter("nationality", OpenApiTypes.STR, description="Filter by nationality (ISO code)"),
        ],
        responses={200: PlayerSerializer(many=True)},
    )
    def get(self, request):
        position = request.query_params.get("position")
        nationality = request.query_params.get("nationality")

        if position:
            queryset = PlayerSelector.list_by_position(position)
        elif nationality:
            queryset = PlayerSelector.list_by_nationality(nationality)
        else:
            queryset = PlayerSelector.list_active()

        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = PlayerSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        tags=["players"],
        summary="Create a player (staff only)",
        request=PlayerSerializer,
        responses={201: PlayerSerializer},
    )
    def post(self, request):
        first_name = request.data.get("first_name", "").strip()
        last_name = request.data.get("last_name", "").strip()

        if not first_name or not last_name:
            return error_response(
                message="first_name and last_name are required.",
                status_code=400,
            )

        try:
            player = PlayerService.create_player(
                first_name=first_name,
                last_name=last_name,
                date_of_birth=request.data.get("date_of_birth"),
                nationality=request.data.get("nationality"),
                primary_position=request.data.get("primary_position", Player.Position.MULTIPLE),
                email=request.data.get("email"),
                phone=request.data.get("phone"),
                height_cm=request.data.get("height_cm"),
                weight_kg=request.data.get("weight_kg"),
                foot=request.data.get("foot"),
                bio=request.data.get("bio"),
                avatar=request.data.get("avatar"),
            )
        except Exception as exc:
            return error_response(message=str(exc), status_code=400)

        serializer = PlayerSerializer(player)
        return success_response(
            data=serializer.data,
            message="Player created successfully.",
            status_code=201,
        )


class PlayerDetailUpdateView(APIView):
    """
    GET:   Get detailed player profile including career history.
    PATCH: Update player profile fields (staff only).
    """

    permission_classes = [IsStaffOrReadOnly]

    @extend_schema(
        tags=["players"],
        summary="Get player detail",
        responses={200: PlayerDetailSerializer},
    )
    def get(self, request, slug: str):
        player = PlayerSelector.get_by_slug(slug)

        if not player:
            return error_response(
                message="Player not found.",
                status_code=404,
            )

        serializer = PlayerDetailSerializer(player)
        return success_response(data=serializer.data, message="Player retrieved successfully.")

    @extend_schema(
        tags=["players"],
        summary="Update player profile (staff only)",
        request=PlayerSerializer,
        responses={200: PlayerSerializer},
    )
    def patch(self, request, slug: str):
        player = PlayerSelector.get_by_slug(slug)

        if not player:
            return error_response(message="Player not found.", status_code=404)

        allowed = {
            "first_name", "last_name", "date_of_birth", "nationality",
            "primary_position", "email", "phone", "height_cm", "weight_kg",
            "foot", "bio", "avatar", "status",
        }
        payload = {k: v for k, v in request.data.items() if k in allowed}

        try:
            player = PlayerService.update_player(player, **payload)
        except Exception as exc:
            return error_response(message=str(exc), status_code=400)

        serializer = PlayerSerializer(player)
        return success_response(data=serializer.data, message="Player updated successfully.")


class PlayerSearchView(APIView):
    """Search players by name (min 2 chars)."""

    permission_classes = [AllowAny]

    @extend_schema(
        tags=["players"],
        summary="Search players by name",
        parameters=[
            OpenApiParameter("q", OpenApiTypes.STR, description="Search query (minimum 2 characters)"),
        ],
        responses={200: PlayerSerializer(many=True)},
    )
    def get(self, request):
        query = request.query_params.get("q", "")

        if not query or len(query) < 2:
            return success_response(
                data=[],
                message="Search query too short (minimum 2 characters).",
            )

        results = PlayerSelector.search(query)
        serializer = PlayerSerializer(results, many=True)
        return success_response(data=serializer.data, message="Search completed.")


class PlayerRegisterView(APIView):
    """
    POST /api/v1/players/{slug}/register/

    Register a player with a club (requires tenant membership).
    The requesting user must be a member of the club's tenant.
    """

    permission_classes = [CanManagePlayerRegistrations]

    @extend_schema(
        tags=["players"],
        summary="Register player at a club",
        responses={201: PlayerRegistrationSerializer},
    )
    def post(self, request, slug: str):
        from clubs.models import Club
        from clubs.selectors import ClubSelector
        from core.models import TenantMembership

        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        club_id = request.data.get("club_id")
        if not club_id:
            return error_response(message="club_id is required.", status_code=400)

        joined_date = request.data.get("joined_date")
        if not joined_date:
            return error_response(message="joined_date is required.", status_code=400)

        try:
            club = Club.objects.get(id=club_id)
        except Club.DoesNotExist:
            return error_response(message="Club not found.", status_code=404)

        # Verify requesting user belongs to the club's tenant
        is_member = TenantMembership.objects.filter(
            user=request.user,
            tenant=club.tenant,
        ).exists()
        if not is_member:
            return error_response(
                message="You do not belong to this club's organization.",
                status_code=403,
            )

        competition = None
        competition_id = request.data.get("competition_id")
        if competition_id:
            from competitions.models import Competition
            try:
                competition = Competition.objects.get(id=competition_id)
            except Competition.DoesNotExist:
                return error_response(message="Competition not found.", status_code=404)

        try:
            registration = PlayerRegistrationService.register_player(
                player=player,
                club=club,
                tenant=club.tenant,
                joined_date=joined_date,
                shirt_number=request.data.get("shirt_number"),
                competition=competition,
            )
        except PlayerRegistrationConflict as exc:
            return error_response(message=str(exc), status_code=409)
        except Exception as exc:
            return error_response(message=str(exc), status_code=400)

        serializer = PlayerRegistrationSerializer(registration)
        return success_response(
            data=serializer.data,
            message="Player registered successfully.",
            status_code=201,
        )
