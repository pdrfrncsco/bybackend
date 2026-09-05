"""
BOLAYETU — Player Views

API endpoints for players (public, global domain).

Public endpoints (no auth required):
    GET    /api/v1/players/              — List active players (searchable and filterable)
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
from players.serializers.player_registration_request import (
    PlayerRegistrationRequestCreateSerializer,
    PlayerRegistrationRequestSerializer,
)
from players.services import NoPlayerProfile, PlayerNotFound, PlayerRegistrationService, PlayerService, PlayerRegistrationConflict
from players.permissions import IsStaffOrReadOnly, CanManagePlayerRegistrations


class PlayerListCreateView(APIView):
    """
    GET:  List all active players. Supports ?search=, ?position=, ?nationality= and ?without_club= filters.
    POST: Create a new player (staff only).
    """

    permission_classes = [IsStaffOrReadOnly]

    @extend_schema(
        tags=["players"],
        summary="List players",
        parameters=[
            OpenApiParameter("search", OpenApiTypes.STR, description="Search by player name or slug"),
            OpenApiParameter("position", OpenApiTypes.STR, description="Filter by position code (gk, cb, st, ...)"),
            OpenApiParameter("nationality", OpenApiTypes.STR, description="Filter by nationality (ISO code)"),
            OpenApiParameter("without_club", OpenApiTypes.BOOL, description="Filter players without any active club registration"),
        ],
        responses={200: PlayerSerializer(many=True)},
    )
    def get(self, request):
        search = request.query_params.get("search", "").strip()
        position = request.query_params.get("position")
        nationality = request.query_params.get("nationality")
        without_club = request.query_params.get("without_club") == "true"

        queryset = PlayerSelector.list_players(
            search=search or None,
            position=position,
            nationality=nationality,
            without_club=without_club,
        )

        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = PlayerSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        tags=["players"],
        summary="Create a player (staff only)",
        description="""
        Create a new global player profile.
        
        DEPRECATION NOTICE:
        - 'email' and 'phone' fields are deprecated. Use POST /api/v1/players/{id}/contacts/ to manage contact info separately.
        - 'avatar' field is deprecated. Use POST /api/v1/players/{id}/avatar/ with file upload to set profile_photo.
        
        Compatibility window: 2 sprints (ends September 2026).
        """,
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

        if not player.is_public:
            if not request.user or not request.user.is_authenticated:
                return error_response(
                    message="Player not found.",
                    status_code=404,
                )
            from players.permissions import CanManagePlayerProfile
            if not CanManagePlayerProfile.can_manage(user=request.user, player=player):
                return error_response(
                    message="Player not found.",
                    status_code=404,
                )

        serializer = PlayerDetailSerializer(player)
        return success_response(data=serializer.data, message="Player retrieved successfully.")

    @extend_schema(
        tags=["players"],
        summary="Update player profile (staff only)",
        description="""
        Update player profile fields.
        
        DEPRECATION NOTICE:
        - 'email' and 'phone' fields are deprecated. Use PATCH /api/v1/players/{id}/contacts/ to manage contact info separately.
        - 'avatar' field is deprecated. Use POST /api/v1/players/{id}/avatar/ with file upload to set profile_photo.
        
        Compatibility window: 2 sprints (ends September 2026).
        """,
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
            OpenApiParameter("without_club", OpenApiTypes.BOOL, description="Filter players without any active club registration"),
        ],
        responses={200: PlayerSerializer(many=True)},
    )
    def get(self, request):
        query = request.query_params.get("q", "")
        without_club = request.query_params.get("without_club") == "true"

        if not query or len(query) < 2:
            return success_response(
                data=[],
                message="Search query too short (minimum 2 characters).",
            )

        results = PlayerSelector.search(query, without_club=without_club)
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
        from clubs.exceptions import NoClubMembership
        from clubs.models import Club
        from clubs.services import ClubService
        from accounts.selectors import TenantMembershipSelector
        from players.services.player_registration_request_service import (
            PlayerRegistrationRequestService,
            DuplicatePlayerRegistrationRequest,
        )

        player = PlayerSelector.get_by_slug(slug)
        if not player:
            return error_response(message="Player not found.", status_code=404)

        input_serializer = PlayerRegistrationRequestCreateSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        club_id = input_serializer.validated_data["club_id"]
        joined_date = input_serializer.validated_data["joined_date"]

        try:
            club = Club.objects.get(id=club_id)
        except Club.DoesNotExist:
            return error_response(message="Club not found.", status_code=404)

        belongs_to_tenant = TenantMembershipSelector.user_belongs_to_tenant(user=request.user, tenant_id=club.tenant_id)

        belongs_to_club = False
        try:
            managed_club = ClubService.get_club_for_user(user=request.user)
            belongs_to_club = managed_club.id == club.id
        except NoClubMembership:
            belongs_to_club = False

        if not (belongs_to_tenant or belongs_to_club):
            return error_response(
                message="You do not belong to this club's organization.",
                status_code=403,
            )

        competition = None
        competition_id = input_serializer.validated_data.get("competition_id")
        if competition_id:
            from competitions.models import Competition
            try:
                competition = Competition.objects.get(id=competition_id)
            except Competition.DoesNotExist:
                return error_response(message="Competition not found.", status_code=404)

        try:
            # Convert direct registration to an invitation
            invitation = PlayerRegistrationRequestService.create_invitation(
                player=player,
                club=club,
                invited_by=request.user,
                joined_date=joined_date,
                shirt_number=input_serializer.validated_data.get("shirt_number"),
                competition=competition,
            )
        except (DuplicatePlayerRegistrationRequest, PlayerRegistrationConflict) as exc:
            return error_response(message=str(exc), status_code=409)
        except Exception as exc:
            return error_response(message=str(exc), status_code=400)

        serializer = PlayerRegistrationRequestSerializer(invitation)
        return success_response(
            data=serializer.data,
            message="Player invitation sent successfully.",
            status_code=201,
        )
