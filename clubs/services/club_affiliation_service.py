import logging

from django.db import transaction
from django.utils import timezone

from accounts.models import User
from clubs.constants import ClubStatus
from clubs.exceptions import DuplicateClubAffiliationRequest, DuplicateClubName
from clubs.models import Club, ClubAffiliationRequest
from clubs.services.club_service import ClubService
from core.models import Tenant

logger = logging.getLogger(__name__)


class ClubAffiliationService:
    @staticmethod
    @transaction.atomic
    def submit_request(
        *,
        tenant: Tenant,
        submitted_by: User | None = None,
        **kwargs,
    ) -> ClubAffiliationRequest:
        if ClubAffiliationRequest.objects.filter(
            tenant=tenant,
            name__iexact=kwargs.get("name", ""),
        ).exists():
            raise DuplicateClubAffiliationRequest()

        request = ClubAffiliationRequest.objects.create(
            tenant=tenant,
            submitted_by=submitted_by,
            **kwargs,
        )
        logger.info("Club affiliation request submitted: %s (%s)", request.name, request.id)
        return request

    @staticmethod
    @transaction.atomic
    def review_request(
        *,
        request_obj: ClubAffiliationRequest,
        reviewed_by: User,
        approve: bool,
        review_notes: str = "",
    ) -> ClubAffiliationRequest:
        if request_obj.status != ClubAffiliationRequest.Status.PENDING:
            raise ValueError("This request has already been reviewed.")

        request_obj.review_notes = review_notes
        request_obj.reviewed_by = reviewed_by
        request_obj.reviewed_at = timezone.now()

        if approve:
            if Club.objects.filter(tenant=request_obj.tenant, name__iexact=request_obj.name).exists():
                raise DuplicateClubName()

            club = ClubService.create_club(
                tenant=request_obj.tenant,
                name=request_obj.name,
                short_name=request_obj.short_name,
                founded_year=request_obj.founded_year,
                city=request_obj.city,
                country=request_obj.country,
                email=request_obj.email,
                phone=request_obj.phone,
                website=request_obj.website,
                description=request_obj.description,
                primary_color=request_obj.primary_color,
                secondary_color=request_obj.secondary_color,
                stadium_name=request_obj.stadium_name,
                stadium_capacity=request_obj.stadium_capacity,
                status=ClubStatus.INACTIVE,
                is_public=True,
                is_verified=False,
            )
            club = ClubService.activate(club=club)
            request_obj.club = club
            request_obj.status = ClubAffiliationRequest.Status.APPROVED
        else:
            request_obj.status = ClubAffiliationRequest.Status.REJECTED

        request_obj.save()
        logger.info("Club affiliation request reviewed: %s (%s)", request_obj.id, request_obj.status)
        return request_obj
