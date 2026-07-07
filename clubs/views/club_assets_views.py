"""
BOLAYETU — Club Assets Views

Endpoints for club documents and sponsors.
"""

from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from accounts.permissions import IsActiveAccount
from clubs.exceptions import ClubNotFound
from clubs.models import Club, ClubDocument, ClubSponsor
from clubs.selectors import ClubSelector
from clubs.serializers import (
    ClubDocumentCreateSerializer,
    ClubDocumentSerializer,
    ClubSponsorCreateSerializer,
    ClubSponsorSerializer,
    ClubSponsorUpdateSerializer,
)
from clubs.services import ClubDocumentService, ClubSponsorService
from clubs.permissions import IsClubAdmin
from common.pagination import StandardPagination
from common.responses import created_response, error_response, not_found_response, success_response


def _get_club(*, slug: str, tenant=None, public_only: bool = False) -> Club:
    if tenant:
        try:
            filters = {"slug": slug, "tenant": tenant}
            if public_only:
                filters["is_public"] = True
            return Club.objects.select_related("tenant").get(**filters)
        except Club.DoesNotExist:
            raise ClubNotFound()

    club = ClubSelector.get_by_slug(slug=slug) if public_only else ClubSelector.get_by_slug_any(slug=slug)
    if club is None:
        raise ClubNotFound()
    return club


class ClubDocumentsView(APIView):
    permission_classes = [IsAuthenticated, IsActiveAccount, IsClubAdmin]

    @extend_schema(tags=["clubs"], request=ClubDocumentCreateSerializer, responses={200: ClubDocumentSerializer(many=True)})
    def get(self, request, slug: str):
        club = _get_club(slug=slug, tenant=getattr(request, "tenant", None))
        documents = ClubSelector.get_documents(club=club)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(documents, request)
        serializer = ClubDocumentSerializer(page if page is not None else documents, many=True)
        if page is not None:
            return paginator.get_paginated_response(serializer.data)
        return success_response(data=serializer.data, message="Club documents retrieved successfully.")

    @extend_schema(tags=["clubs"], request=ClubDocumentCreateSerializer, responses={201: ClubDocumentSerializer})
    def post(self, request, slug: str):
        club = _get_club(slug=slug, tenant=getattr(request, "tenant", None))

        serializer = ClubDocumentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        document = ClubDocumentService.upload_document(
            club=club,
            tenant=club.tenant,
            title=serializer.validated_data["title"],
            category=serializer.validated_data["category"],
            document=serializer.validated_data["document"],
            description=serializer.validated_data.get("description", ""),
            is_public=serializer.validated_data.get("is_public", False),
            valid_until=serializer.validated_data.get("valid_until"),
            uploaded_by=request.user,
        )
        return created_response(data=ClubDocumentSerializer(document).data, message="Club document uploaded successfully.")


class ClubDocumentDetailView(APIView):
    permission_classes = [IsAuthenticated, IsActiveAccount, IsClubAdmin]

    @extend_schema(tags=["clubs"], responses={200: ClubDocumentSerializer})
    def delete(self, request, slug: str, document_id):
        club = _get_club(slug=slug, tenant=getattr(request, "tenant", None))
        try:
            document = ClubDocument.objects.select_related("asset").get(id=document_id, club=club)
        except ClubDocument.DoesNotExist:
            return not_found_response(message="Club document not found.")

        ClubDocumentService.remove_document(document=document)
        return success_response(message="Club document deleted successfully.")


class ClubPublicDocumentsView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(tags=["clubs"], responses={200: ClubDocumentSerializer(many=True)})
    def get(self, request, slug: str):
        club = _get_club(slug=slug, tenant=getattr(request, "tenant", None), public_only=True)
        documents = ClubSelector.get_public_documents(club=club)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(documents, request)
        serializer = ClubDocumentSerializer(page if page is not None else documents, many=True)
        if page is not None:
            return paginator.get_paginated_response(serializer.data)
        return success_response(data=serializer.data, message="Club documents retrieved successfully.")


class ClubSponsorsView(APIView):
    permission_classes = [IsAuthenticated, IsActiveAccount, IsClubAdmin]

    @extend_schema(tags=["clubs"], request=ClubSponsorCreateSerializer, responses={200: ClubSponsorSerializer(many=True)})
    def get(self, request, slug: str):
        club = _get_club(slug=slug, tenant=getattr(request, "tenant", None))
        sponsors = ClubSelector.get_sponsors(club=club)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(sponsors, request)
        serializer = ClubSponsorSerializer(page if page is not None else sponsors, many=True)
        if page is not None:
            return paginator.get_paginated_response(serializer.data)
        return success_response(data=serializer.data, message="Club sponsors retrieved successfully.")

    @extend_schema(tags=["clubs"], request=ClubSponsorCreateSerializer, responses={201: ClubSponsorSerializer})
    def post(self, request, slug: str):
        club = _get_club(slug=slug, tenant=getattr(request, "tenant", None))

        serializer = ClubSponsorCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        sponsor = ClubSponsorService.create_sponsor(
            club=club,
            tenant=club.tenant,
            name=serializer.validated_data["name"],
            sponsor_type=serializer.validated_data["sponsor_type"],
            description=serializer.validated_data.get("description", ""),
            website=serializer.validated_data.get("website"),
            logo=serializer.validated_data.get("logo"),
            is_active=serializer.validated_data.get("is_active", True),
            sort_order=serializer.validated_data.get("sort_order", 0),
            uploaded_by=request.user,
        )
        return created_response(data=ClubSponsorSerializer(sponsor).data, message="Club sponsor created successfully.")


class ClubSponsorDetailView(APIView):
    permission_classes = [IsAuthenticated, IsActiveAccount, IsClubAdmin]

    @extend_schema(tags=["clubs"], responses={200: ClubSponsorSerializer})
    def patch(self, request, slug: str, sponsor_id):
        club = _get_club(slug=slug, tenant=getattr(request, "tenant", None))
        try:
            sponsor = ClubSponsor.objects.select_related("logo_asset").get(id=sponsor_id, club=club)
        except ClubSponsor.DoesNotExist:
            return not_found_response(message="Club sponsor not found.")

        serializer = ClubSponsorUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        sponsor.name = serializer.validated_data.get("name", sponsor.name)
        sponsor.sponsor_type = serializer.validated_data.get("sponsor_type", sponsor.sponsor_type)
        sponsor.description = serializer.validated_data.get("description", sponsor.description)
        sponsor.website = serializer.validated_data.get("website", sponsor.website)
        sponsor.is_active = serializer.validated_data.get("is_active", sponsor.is_active)
        sponsor.sort_order = serializer.validated_data.get("sort_order", sponsor.sort_order)
        if serializer.validated_data.get("logo") is not None:
            old_logo_asset_id = sponsor.logo_asset_id
            from media_assets.constants import AssetCategory, AssetVisibility, OwnerType
            from media_assets.services import MediaAssetService

            sponsor.logo_asset = MediaAssetService.upload_for_owner(
                file=serializer.validated_data["logo"],
                owner_type=OwnerType.CLUB,
                owner_id=club.id,
                role=AssetCategory.SPONSOR_LOGO,
                name=f"{sponsor.name} Logo",
                tenant=club.tenant,
                uploaded_by=request.user,
                visibility=AssetVisibility.PUBLIC,
                images_only=True,
            )
            if old_logo_asset_id and old_logo_asset_id != sponsor.logo_asset_id:
                try:
                    MediaAssetService.delete_asset(asset_id=str(old_logo_asset_id))
                except Exception:
                    pass
        sponsor.save()
        return success_response(data=ClubSponsorSerializer(sponsor).data, message="Club sponsor updated successfully.")

    @extend_schema(tags=["clubs"], responses={200: ClubSponsorSerializer})
    def delete(self, request, slug: str, sponsor_id):
        club = _get_club(slug=slug, tenant=getattr(request, "tenant", None))
        try:
            sponsor = ClubSponsor.objects.select_related("logo_asset").get(id=sponsor_id, club=club)
        except ClubSponsor.DoesNotExist:
            return not_found_response(message="Club sponsor not found.")

        ClubSponsorService.delete_sponsor(sponsor=sponsor)
        return success_response(message="Club sponsor deleted successfully.")


class ClubPublicSponsorsView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(tags=["clubs"], responses={200: ClubSponsorSerializer(many=True)})
    def get(self, request, slug: str):
        club = _get_club(slug=slug, tenant=getattr(request, "tenant", None), public_only=True)
        sponsors = ClubSelector.get_public_sponsors(club=club)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(sponsors, request)
        serializer = ClubSponsorSerializer(page if page is not None else sponsors, many=True)
        if page is not None:
            return paginator.get_paginated_response(serializer.data)
        return success_response(data=serializer.data, message="Club sponsors retrieved successfully.")
