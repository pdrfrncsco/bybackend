"""
BOLAYETU — Club Views

API endpoints for club management.

Endpoints:
    Authenticated (club admin):
        GET    /api/v1/clubs/me/                    — Get own club
        PATCH  /api/v1/clubs/me/                    — Update own club
        POST   /api/v1/clubs/me/logo/               — Upload logo
        POST   /api/v1/clubs/                       — Create a club (org admin)
        POST   /api/v1/clubs/:slug/activate/        — Activate club
        POST   /api/v1/clubs/:slug/suspend/         — Suspend club
        GET    /api/v1/clubs/:slug/members/         — List members
        POST   /api/v1/clubs/:slug/members/         — Add member
        PATCH  /api/v1/clubs/:slug/members/:id/     — Update member
        DELETE /api/v1/clubs/:slug/members/:id/     — Remove member

    Public (anyone):
        GET    /api/v1/clubs/public/                 — List public clubs
        GET    /api/v1/clubs/public/:slug/           — Get public club details
        GET    /api/v1/clubs/public/:slug/kpis/      — Get KPIs
        GET    /api/v1/clubs/public/:slug/squad/     — Get squad (players)
        GET    /api/v1/clubs/public/:slug/staff/     — Get staff
"""

import logging

from django.db.models import Q
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from accounts.permissions import IsActiveAccount
from clubs.exceptions import (
    ClubMemberNotFound,
    ClubNotFound,
    NoClubMembership,
)
from clubs.models import Club
from clubs.permissions import (
    CanViewPublicClub,
    IsClubAdmin,
)
from clubs.selectors import ClubSelector
from clubs.serializers import (
    ClubCreateSerializer,
    ClubKpisSerializer,
    ClubLogoUploadSerializer,
    ClubMemberSerializer,
    ClubSerializer,
    ClubSquadMemberSerializer,
    ClubStaffSerializer,
    ClubUpdateSerializer,
    PublicClubSerializer,
)
from clubs.services import ClubService
from common.pagination import StandardPagination
from common.responses import created_response, error_response, success_response

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────
# Authenticated Club Management (Admin)
# ─────────────────────────────────────────────────────────────────────


class ClubMeView(APIView):
    """
    Retrieve or update the authenticated user's club.
    """

    permission_classes = [IsAuthenticated, IsActiveAccount]

    @extend_schema(
        tags=["clubs"],
        responses={200: ClubSerializer},
    )
    def get(self, request):
        club = ClubService.get_club_for_user(user=request.user)
        serializer = ClubSerializer(club)
        return success_response(
            data=serializer.data,
            message="Club retrieved successfully.",
        )

    @extend_schema(
        tags=["clubs"],
        request=ClubUpdateSerializer,
        responses={200: ClubSerializer},
    )
    def patch(self, request):
        club = ClubService.get_club_for_user(user=request.user)

        ClubService.assert_is_club_admin(user=request.user, club=club)

        serializer = ClubUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        club = ClubService.update_club(
            club=club,
            **serializer.validated_data,
        )

        return success_response(
            data=ClubSerializer(club).data,
            message="Club updated successfully.",
        )


class ClubLogoView(APIView):
    """
    Upload a logo for the authenticated user's club.
    """

    permission_classes = [IsAuthenticated, IsActiveAccount, IsClubAdmin]

    @extend_schema(
        tags=["clubs"],
        request=ClubLogoUploadSerializer,
        responses={200: ClubSerializer},
    )
    def post(self, request):
        club = ClubService.get_club_for_user(user=request.user)

        file = request.FILES.get("logo")
        if not file:
            return error_response(
                message="No logo file provided.",
                status_code=400,
            )

        club = ClubService.upload_logo(club=club, file=file)

        return success_response(
            data=ClubSerializer(club).data,
            message="Logo uploaded successfully.",
        )


class ClubCreateView(APIView):
    """
    Create a new club within the authenticated user's organization.
    """

    permission_classes = [IsAuthenticated, IsActiveAccount, IsClubAdmin]

    @extend_schema(
        tags=["clubs"],
        request=ClubCreateSerializer,
        responses={201: ClubSerializer},
    )
    def post(self, request):
        from organizations.services import OrganizationService

        tenant = OrganizationService.get_organization_for_user(user=request.user)

        serializer = ClubCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        club = ClubService.create_club(
            tenant=tenant,
            **serializer.validated_data,
        )

        return created_response(
            data=ClubSerializer(club).data,
            message="Club created successfully.",
        )


class ClubActivateView(APIView):
    """Activate a club."""

    permission_classes = [IsAuthenticated, IsActiveAccount, IsClubAdmin]

    @extend_schema(tags=["clubs"], responses={200: ClubSerializer})
    def post(self, request, slug: str):
        club = ClubSelector.get_by_slug_any(slug=slug)
        if club is None:
            raise ClubNotFound()

        ClubService.assert_is_club_admin(user=request.user, club=club)
        club = ClubService.activate(club=club)

        return success_response(
            data=ClubSerializer(club).data,
            message="Club activated successfully.",
        )


class ClubSuspendView(APIView):
    """Suspend a club."""

    permission_classes = [IsAuthenticated, IsActiveAccount, IsClubAdmin]

    @extend_schema(tags=["clubs"], responses={200: ClubSerializer})
    def post(self, request, slug: str):
        club = ClubSelector.get_by_slug_any(slug=slug)
        if club is None:
            raise ClubNotFound()

        ClubService.assert_is_club_admin(user=request.user, club=club)
        club = ClubService.suspend(club=club)

        return success_response(
            data=ClubSerializer(club).data,
            message="Club suspended successfully.",
        )


# ─────────────────────────────────────────────────────────────────────
# Club Member Management (Admin)
# ─────────────────────────────────────────────────────────────────────


class ClubMembersView(APIView):
    """
    List all members of a club or add a new member.
    """

    permission_classes = [IsAuthenticated, IsActiveAccount, IsClubAdmin]

    @extend_schema(tags=["clubs"], responses={200: ClubMemberSerializer(many=True)})
    def get(self, request, slug: str):
        club = ClubSelector.get_by_slug_any(slug=slug)
        if club is None:
            raise ClubNotFound()

        members = ClubSelector.get_members(club=club)
        serializer = ClubMemberSerializer(members, many=True)
        return success_response(
            data=serializer.data,
            message="Club members retrieved successfully.",
        )

    @extend_schema(tags=["clubs"], request=ClubMemberSerializer, responses={201: ClubMemberSerializer})
    def post(self, request, slug: str):
        club = ClubSelector.get_by_slug_any(slug=slug)
        if club is None:
            raise ClubNotFound()

        ClubService.assert_is_club_admin(user=request.user, club=club)

        serializer = ClubMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        member = ClubService.add_member(
            club=club,
            user=serializer.validated_data.get("user"),
            full_name=serializer.validated_data.get("full_name"),
            role=serializer.validated_data.get("role", "player"),
            jersey_number=serializer.validated_data.get("jersey_number"),
            position=serializer.validated_data.get("position"),
            joined_at=serializer.validated_data.get("joined_at"),
        )

        return created_response(
            data=ClubMemberSerializer(member).data,
            message="Member added successfully.",
        )


class ClubMemberDetailView(APIView):
    """
    Update or remove a club member.
    """

    permission_classes = [IsAuthenticated, IsActiveAccount, IsClubAdmin]

    @extend_schema(tags=["clubs"], request=ClubMemberSerializer, responses={200: ClubMemberSerializer})
    def patch(self, request, slug: str, member_id: str):
        club = ClubSelector.get_by_slug_any(slug=slug)
        if club is None:
            raise ClubNotFound()

        member = ClubSelector.get_member_by_id(member_id=member_id)
        if member is None or member.club_id != club.id:
            raise ClubMemberNotFound()

        ClubService.assert_is_club_admin(user=request.user, club=club)

        serializer = ClubMemberSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        member = ClubService.update_member(
            member=member,
            **serializer.validated_data,
        )

        return success_response(
            data=ClubMemberSerializer(member).data,
            message="Member updated successfully.",
        )

    @extend_schema(tags=["clubs"])
    def delete(self, request, slug: str, member_id: str):
        club = ClubSelector.get_by_slug_any(slug=slug)
        if club is None:
            raise ClubNotFound()

        member = ClubSelector.get_member_by_id(member_id=member_id)
        if member is None or member.club_id != club.id:
            raise ClubMemberNotFound()

        ClubService.assert_is_club_admin(user=request.user, club=club)
        ClubService.remove_member(member=member)

        return success_response(
            message="Member removed successfully.",
        )


# ─────────────────────────────────────────────────────────────────────
# Public Club Endpoints
# ─────────────────────────────────────────────────────────────────────


class ClubPublicListView(APIView):
    """
    List all public, active clubs.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        tags=["clubs"],
        responses={200: PublicClubSerializer(many=True)},
    )
    def get(self, request):
        search = request.query_params.get("search")
        tenant_slug = request.query_params.get("organization")

        queryset = ClubSelector.list_public(search=search, tenant_slug=tenant_slug)

        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = PublicClubSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class ClubPublicDetailView(APIView):
    """
    Retrieve details of a public club by slug or UUID.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        tags=["clubs"],
        responses={200: PublicClubSerializer},
    )
    def get(self, request, slug: str):
        # Prefer tenant resolved by subdomain when available
        tenant = getattr(request, "tenant", None)
        if tenant:
            try:
                club = Club.objects.select_related("tenant").get(
                    Q(slug=slug) | Q(id=slug),  # Accept both slug and UUID
                    tenant=tenant,
                    is_public=True
                )
            except Club.DoesNotExist:
                raise ClubNotFound()
        else:
            # Try by slug first, then by UUID
            club = ClubSelector.get_by_slug(slug=slug)
            if club is None:
                try:
                    club = Club.objects.select_related("tenant").get(id=slug, is_public=True)
                except Club.DoesNotExist:
                    raise ClubNotFound()

        serializer = PublicClubSerializer(club)
        return success_response(
            data=serializer.data,
            message="Club retrieved successfully.",
        )


class ClubKpisView(APIView):
    """Retrieve KPI statistics for a public club by slug or UUID."""

    permission_classes = [AllowAny]

    @extend_schema(tags=["clubs"], responses={200: ClubKpisSerializer})
    def get(self, request, slug: str):
        tenant = getattr(request, "tenant", None)
        if tenant:
            try:
                club = Club.objects.select_related("tenant").get(
                    Q(slug=slug) | Q(id=slug),
                    tenant=tenant,
                    is_public=True
                )
            except Club.DoesNotExist:
                raise ClubNotFound()
        else:
            club = ClubSelector.get_by_slug(slug=slug)
            if club is None:
                try:
                    club = Club.objects.select_related("tenant").get(id=slug, is_public=True)
                except Club.DoesNotExist:
                    raise ClubNotFound()

        kpis = ClubSelector.get_kpis(club=club)
        serializer = ClubKpisSerializer(kpis)
        return success_response(
            data=serializer.data,
            message="Club KPIs retrieved successfully.",
        )


class ClubSquadView(APIView):
    """Retrieve the squad (players) for a public club by slug or UUID."""

    permission_classes = [AllowAny]

    @extend_schema(tags=["clubs"], responses={200: ClubSquadMemberSerializer(many=True)})
    def get(self, request, slug: str):
        tenant = getattr(request, "tenant", None)
        if tenant:
            try:
                club = Club.objects.select_related("tenant").get(
                    Q(slug=slug) | Q(id=slug),
                    tenant=tenant,
                    is_public=True
                )
            except Club.DoesNotExist:
                raise ClubNotFound()
        else:
            club = ClubSelector.get_by_slug(slug=slug)
            if club is None:
                try:
                    club = Club.objects.select_related("tenant").get(id=slug, is_public=True)
                except Club.DoesNotExist:
                    raise ClubNotFound()

        squad = ClubSelector.get_squad(club=club)
        serializer = ClubSquadMemberSerializer(squad, many=True)
        return success_response(
            data=serializer.data,
            message="Club squad retrieved successfully.",
        )


class ClubStaffView(APIView):
    """Retrieve the staff for a public club by slug or UUID."""

    permission_classes = [AllowAny]

    @extend_schema(tags=["clubs"], responses={200: ClubStaffSerializer(many=True)})
    def get(self, request, slug: str):
        tenant = getattr(request, "tenant", None)
        if tenant:
            try:
                club = Club.objects.select_related("tenant").get(
                    Q(slug=slug) | Q(id=slug),
                    tenant=tenant,
                    is_public=True
                )
            except Club.DoesNotExist:
                raise ClubNotFound()
        else:
            club = ClubSelector.get_by_slug(slug=slug)
            if club is None:
                try:
                    club = Club.objects.select_related("tenant").get(id=slug, is_public=True)
                except Club.DoesNotExist:
                    raise ClubNotFound()

        staff = ClubSelector.get_staff(club=club)
        serializer = ClubStaffSerializer(staff, many=True)
        return success_response(
            data=serializer.data,
            message="Club staff retrieved successfully.",
        )


# ─────────────────────────────────────────────────────────────────────
# Club Competitions, Matches & Standings Endpoints
# ─────────────────────────────────────────────────────────────────────


class ClubPublicCompetitionsView(APIView):
    """Retrieve public competitions linked to a club by slug or UUID."""

    permission_classes = [AllowAny]

    @extend_schema(tags=["clubs"])
    def get(self, request, slug: str):
        tenant = getattr(request, "tenant", None)
        if tenant:
            try:
                club = Club.objects.select_related("tenant").get(
                    Q(slug=slug) | Q(id=slug),
                    tenant=tenant,
                    is_public=True
                )
            except Club.DoesNotExist:
                raise ClubNotFound()
        else:
            club = ClubSelector.get_by_slug(slug=slug)
            if club is None:
                try:
                    club = Club.objects.select_related("tenant").get(id=slug, is_public=True)
                except Club.DoesNotExist:
                    raise ClubNotFound()

        from competitions.serializers import CompetitionSerializer

        competitions = ClubSelector.get_competitions(club=club)
        serializer = CompetitionSerializer(competitions, many=True)
        return success_response(
            data=serializer.data,
            message="Club competitions retrieved successfully.",
        )


class ClubPublicMatchesView(APIView):
    """Retrieve public matches for a club by slug or UUID."""

    permission_classes = [AllowAny]

    @extend_schema(tags=["clubs"])
    def get(self, request, slug: str):
        tenant = getattr(request, "tenant", None)
        if tenant:
            try:
                club = Club.objects.select_related("tenant").get(
                    Q(slug=slug) | Q(id=slug),
                    tenant=tenant,
                    is_public=True
                )
            except Club.DoesNotExist:
                raise ClubNotFound()
        else:
            club = ClubSelector.get_by_slug(slug=slug)
            if club is None:
                try:
                    club = Club.objects.select_related("tenant").get(id=slug, is_public=True)
                except Club.DoesNotExist:
                    raise ClubNotFound()

        from competitions.serializers import MatchSerializer

        status = request.query_params.get("status")
        competition_id = request.query_params.get("competition_id")

        matches = ClubSelector.get_matches(club=club, status=status, competition_id=competition_id)
        serializer = MatchSerializer(matches, many=True)
        return success_response(
            data=serializer.data,
            message="Club matches retrieved successfully.",
        )


class ClubPublicStandingsView(APIView):
    """Retrieve public standings for competitions involving a club by slug or UUID."""

    permission_classes = [AllowAny]

    @extend_schema(tags=["clubs"])
    def get(self, request, slug: str):
        tenant = getattr(request, "tenant", None)
        if tenant:
            try:
                club = Club.objects.select_related("tenant").get(
                    Q(slug=slug) | Q(id=slug),
                    tenant=tenant,
                    is_public=True
                )
            except Club.DoesNotExist:
                raise ClubNotFound()
        else:
            club = ClubSelector.get_by_slug(slug=slug)
            if club is None:
                try:
                    club = Club.objects.select_related("tenant").get(id=slug, is_public=True)
                except Club.DoesNotExist:
                    raise ClubNotFound()

        from competitions.serializers import StandingSerializer

        competition_id = request.query_params.get("competition_id")

        standings = ClubSelector.get_standings(club=club, competition_id=competition_id)
        serializer = StandingSerializer(standings, many=True)
        return success_response(
            data=serializer.data,
            message="Club standings retrieved successfully.",
        )


class ClubMeCompetitionsView(APIView):
    """Retrieve competitions for the authenticated user's club."""

    permission_classes = [IsAuthenticated, IsActiveAccount]

    @extend_schema(tags=["clubs"])
    def get(self, request):
        club = ClubService.get_club_for_user(user=request.user)

        from competitions.serializers import CompetitionSerializer

        competitions = ClubSelector.get_competitions(club=club)
        serializer = CompetitionSerializer(competitions, many=True)
        return success_response(
            data=serializer.data,
            message="Club competitions retrieved successfully.",
        )


class ClubMeMatchesView(APIView):
    """Retrieve matches for the authenticated user's club."""

    permission_classes = [IsAuthenticated, IsActiveAccount]

    @extend_schema(tags=["clubs"])
    def get(self, request):
        club = ClubService.get_club_for_user(user=request.user)

        from competitions.serializers import MatchSerializer

        status = request.query_params.get("status")
        competition_id = request.query_params.get("competition_id")

        matches = ClubSelector.get_matches(club=club, status=status, competition_id=competition_id)
        serializer = MatchSerializer(matches, many=True)
        return success_response(
            data=serializer.data,
            message="Club matches retrieved successfully.",
        )


class ClubMeStandingsView(APIView):
    """Retrieve standings for the authenticated user's club."""

    permission_classes = [IsAuthenticated, IsActiveAccount]

    @extend_schema(tags=["clubs"])
    def get(self, request):
        club = ClubService.get_club_for_user(user=request.user)

        from competitions.serializers import StandingSerializer

        competition_id = request.query_params.get("competition_id")

        standings = ClubSelector.get_standings(club=club, competition_id=competition_id)
        serializer = StandingSerializer(standings, many=True)
        return success_response(
            data=serializer.data,
            message="Club standings retrieved successfully.",
        )

