import logging

from django.db import transaction
from django.utils import timezone

from accounts.models import User
from clubs.constants import ClubMemberRole, ClubStatus
from clubs.exceptions import DuplicateClubAffiliationRequest, DuplicateClubName
from clubs.models import Club, ClubAffiliationRequest, ClubMember
from clubs.services.club_service import ClubService
from core.models import Tenant

logger = logging.getLogger(__name__)


class ClubAffiliationService:
    @staticmethod
    def _ensure_club_for_request(*, request_obj: ClubAffiliationRequest) -> Club:
        club = request_obj.club

        if club is None:
            club = Club.objects.filter(
                tenant=request_obj.tenant,
                name__iexact=request_obj.name,
            ).first()

        if club is None:
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

        # Do not auto-activate or assign membership upon request submission.
        # Activation and membership assignment should occur only after an admin approves the request.

        if request_obj.club_id != club.id:
            request_obj.club = club

        return club

    @staticmethod
    @transaction.atomic
    def submit_request(
        *,
        tenant: Tenant,
        submitted_by: User | None = None,
        is_draft: bool = False,
        **kwargs,
    ) -> ClubAffiliationRequest:
        if ClubAffiliationRequest.objects.filter(
            tenant=tenant,
            name__iexact=kwargs.get("name", ""),
        ).exists():
            raise DuplicateClubAffiliationRequest()

        status = ClubAffiliationRequest.Status.DRAFT if is_draft else ClubAffiliationRequest.Status.PENDING

        request = ClubAffiliationRequest.objects.create(
            tenant=tenant,
            submitted_by=submitted_by,
            status=status,
            **kwargs,
        )
        # Ensure a provisional club exists for the request so it can be shown / edited by the submitter.
        ClubAffiliationService._ensure_club_for_request(request_obj=request)
        # If this is a draft, give the submitter admin membership on the provisional club
        if is_draft and request.submitted_by_id:
            ClubMember.objects.update_or_create(
                club=request.club,
                user=request.submitted_by,
                defaults={
                    "role": ClubMemberRole.PRESIDENT,
                    "is_active": True,
                },
            )

        # Persist the club reference on the request (if it was set).
        request.save(update_fields=["club"])  # type: ignore[arg-type]
        logger.info("Club affiliation request created (draft=%s): %s (%s)", is_draft, request.name, request.id)
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
        # Repair case: already approved but missing club reference
        if request_obj.status == ClubAffiliationRequest.Status.APPROVED and request_obj.club_id is None:
            club = ClubAffiliationService._ensure_club_for_request(request_obj=request_obj)
            # Activate and assign membership if needed
            if club.status != ClubStatus.ACTIVE:
                ClubService.activate(club=club)
            if request_obj.submitted_by_id:
                ClubMember.objects.update_or_create(
                    club=club,
                    user=request_obj.submitted_by,
                    defaults={
                        "role": ClubMemberRole.PRESIDENT,
                        "is_active": True,
                    },
                )
            request_obj.save(update_fields=["club", "updated_at"])
            logger.info("Approved club affiliation request repaired: %s", request_obj.id)
            return request_obj

        if request_obj.status != ClubAffiliationRequest.Status.PENDING:
            raise ValueError("This request has already been reviewed.")

        request_obj.review_notes = review_notes
        request_obj.reviewed_by = reviewed_by
        request_obj.reviewed_at = timezone.now()

        if approve:
            existing_club = Club.objects.filter(tenant=request_obj.tenant, name__iexact=request_obj.name).first()
            if existing_club is not None and request_obj.club_id not in (None, existing_club.id):
                raise DuplicateClubName()

            club = ClubAffiliationService._ensure_club_for_request(request_obj=request_obj)
            # Activate the club and assign the submitter as president
            if club.status != ClubStatus.ACTIVE:
                ClubService.activate(club=club)
            if request_obj.submitted_by_id:
                ClubMember.objects.update_or_create(
                    club=club,
                    user=request_obj.submitted_by,
                    defaults={
                        "role": ClubMemberRole.PRESIDENT,
                        "is_active": True,
                    },
                )

            request_obj.status = ClubAffiliationRequest.Status.APPROVED
        else:
            request_obj.status = ClubAffiliationRequest.Status.REJECTED

        request_obj.save()
        logger.info("Club affiliation request reviewed: %s (%s)", request_obj.id, request_obj.status)
        return request_obj
