import logging
from datetime import date

from django.db import transaction
from django.utils import timezone

from accounts.models import User
from clubs.models import Club
from players.models import Player, PlayerRegistration, PlayerRegistrationRequest
from players.services import PlayerRegistrationConflict, PlayerRegistrationService

logger = logging.getLogger(__name__)


class DuplicatePlayerRegistrationRequest(Exception):
    """Raised when an identical pending request already exists."""


class PlayerRegistrationRequestService:
    @staticmethod
    @transaction.atomic
    def submit_request(
        *,
        player: Player,
        club: Club,
        submitted_by: User | None,
        joined_date: date,
        shirt_number: int | None = None,
        competition=None,
    ) -> PlayerRegistrationRequest:
        # Check if player has any active registration
        active_reg = PlayerRegistration.objects.filter(
            player=player,
            status__in=[
                PlayerRegistration.RegistrationStatus.REGISTERED,
                PlayerRegistration.RegistrationStatus.LOANED,
            ],
        ).select_related("club").first()
        if active_reg:
            raise PlayerRegistrationConflict(
                f"{player.full_name} is already actively registered at {active_reg.club.name}."
            )

        pending_qs = PlayerRegistrationRequest.objects.filter(
            player=player,
            club=club,
            competition=competition,
            status=PlayerRegistrationRequest.Status.PENDING,
        )
        if pending_qs.exists():
            raise DuplicatePlayerRegistrationRequest(
                "A pending registration request already exists for this player and club."
            )

        request = PlayerRegistrationRequest.objects.create(
            player=player,
            club=club,
            tenant=club.tenant,
            competition=competition,
            submitted_by=submitted_by,
            joined_date=joined_date,
            shirt_number=shirt_number,
        )
        logger.info(
            "Player registration request submitted: %s → %s (%s)",
            player.full_name,
            club.name,
            request.id,
        )
        return request

    @staticmethod
    @transaction.atomic
    def review_request(
        *,
        request_obj: PlayerRegistrationRequest,
        reviewed_by: User,
        approve: bool,
        review_notes: str = "",
    ) -> PlayerRegistrationRequest:
        if request_obj.status != PlayerRegistrationRequest.Status.PENDING:
            raise ValueError("This request has already been reviewed.")

        request_obj.review_notes = review_notes
        request_obj.reviewed_by = reviewed_by
        request_obj.reviewed_at = timezone.now()

        if approve:
            try:
                registration = PlayerRegistrationService.register_player(
                    player=request_obj.player,
                    club=request_obj.club,
                    tenant=request_obj.tenant,
                    joined_date=request_obj.joined_date,
                    shirt_number=request_obj.shirt_number,
                    competition=request_obj.competition,
                )
            except PlayerRegistrationConflict as exc:
                raise ValueError(str(exc)) from exc

            request_obj.registration = registration
            request_obj.status = PlayerRegistrationRequest.Status.APPROVED
        else:
            request_obj.status = PlayerRegistrationRequest.Status.REJECTED

        request_obj.save()
        logger.info(
            "Player registration request reviewed: %s (%s)",
            request_obj.id,
            request_obj.status,
        )
        return request_obj
