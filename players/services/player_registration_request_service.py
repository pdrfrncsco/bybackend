import logging
from datetime import date

from django.db import IntegrityError, transaction
from django.utils import timezone

from accounts.models import User
from clubs.models import Club
from competitions.constants import CompetitionStatus
from competitions.models import Competition, CompetitionRegistration
from players.models import Player, PlayerRegistration, PlayerRegistrationRequest
from players.events.types import (
    PLAYER_REGISTRATION_INVITATION_ACCEPTED,
    PLAYER_REGISTRATION_INVITATION_CREATED,
    PLAYER_REGISTRATION_INVITATION_REJECTED,
    PLAYER_REGISTRATION_REQUEST_APPROVED,
    PLAYER_REGISTRATION_REQUEST_REJECTED,
    PLAYER_REGISTRATION_REQUEST_SUBMITTED,
    publish_registration_request_event,
)
from players.services import PlayerRegistrationConflict, PlayerRegistrationService

logger = logging.getLogger(__name__)


class DuplicatePlayerRegistrationRequest(Exception):
    """Raised when an identical pending request already exists."""


class RequestAlreadyReviewed(Exception):
    """Raised when a request has left the state that can be reviewed."""


class PlayerRegistrationRequestService:
    @staticmethod
    def _validate_competition(*, club: Club, competition: Competition | None) -> None:
        if competition is None:
            return

        if competition.tenant_id != club.tenant_id or competition.status != CompetitionStatus.ACTIVE:
            raise ValueError("Competition is not available for this club.")

        if not CompetitionRegistration.objects.filter(
            competition=competition,
            club=club,
            tenant_id=club.tenant_id,
        ).exists():
            raise ValueError("Competition is not registered for this club.")

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
        """
        Player requests to join a club.
        """
        PlayerRegistrationRequestService._validate_competition(club=club, competition=competition)

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

        try:
            # A savepoint lets us translate a database race into the same
            # domain result as the optimistic check above.
            with transaction.atomic():
                request = PlayerRegistrationRequest.objects.create(
                    player=player,
                    club=club,
                    tenant=club.tenant,
                    competition=competition,
                    submitted_by=submitted_by,
                    joined_date=joined_date,
                    shirt_number=shirt_number,
                )
        except IntegrityError as exc:
            raise DuplicatePlayerRegistrationRequest(
                "A pending registration request already exists for this player and club."
            ) from exc
        logger.info(
            "Player registration request submitted: %s → %s (%s)",
            player.full_name,
            club.name,
            request.id,
        )
        publish_registration_request_event(
            PLAYER_REGISTRATION_REQUEST_SUBMITTED, request, actor_id=submitted_by.id if submitted_by else None
        )
        return request

    @staticmethod
    @transaction.atomic
    def create_invitation(
        *,
        player: Player,
        club: Club,
        invited_by: User,
        joined_date: date,
        shirt_number: int | None = None,
        competition=None,
    ) -> PlayerRegistrationRequest:
        """
        Club invites a player to join.
        """
        PlayerRegistrationRequestService._validate_competition(club=club, competition=competition)

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

        # Prevent duplicate invitations
        pending_invitation = PlayerRegistrationRequest.objects.filter(
            player=player,
            club=club,
            competition=competition,
            status=PlayerRegistrationRequest.Status.INVITED,
        ).exists()
        if pending_invitation:
            raise DuplicatePlayerRegistrationRequest(
                "An active invitation already exists for this player and club."
            )

        try:
            with transaction.atomic():
                request = PlayerRegistrationRequest.objects.create(
                    player=player,
                    club=club,
                    tenant=club.tenant,
                    competition=competition,
                    submitted_by=invited_by,
                    joined_date=joined_date,
                    shirt_number=shirt_number,
                    status=PlayerRegistrationRequest.Status.INVITED,
                )
        except IntegrityError as exc:
            raise DuplicatePlayerRegistrationRequest(
                "An active invitation already exists for this player and club."
            ) from exc
        logger.info(
            "Player invitation created: %s → %s (%s)",
            club.name,
            player.full_name,
            request.id,
        )
        publish_registration_request_event(
            PLAYER_REGISTRATION_INVITATION_CREATED, request, actor_id=invited_by.id
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
        """
        Club reviews a PENDING request.
        """
        # The view may have fetched this object before another reviewer made a
        # decision. Lock and reload it inside the transaction before checking
        # its state, so only one decision can win.
        request_obj = PlayerRegistrationRequest.objects.select_for_update().get(pk=request_obj.pk)
        if request_obj.status != PlayerRegistrationRequest.Status.PENDING:
            raise RequestAlreadyReviewed("This registration request has already been reviewed.")

        request_obj.review_notes = review_notes
        request_obj.reviewed_by = reviewed_by
        request_obj.reviewed_at = timezone.now()

        if approve:
            # Club approves, but registration only created after player acceptance
            request_obj.status = PlayerRegistrationRequest.Status.APPROVED
        else:
            request_obj.status = PlayerRegistrationRequest.Status.REJECTED

        request_obj.save()
        logger.info(
            "Player registration request reviewed: %s (%s)",
            request_obj.id,
            request_obj.status,
        )
        publish_registration_request_event(
            PLAYER_REGISTRATION_REQUEST_APPROVED if approve else PLAYER_REGISTRATION_REQUEST_REJECTED,
            request_obj,
            actor_id=reviewed_by.id,
        )
        return request_obj

    @staticmethod
    @transaction.atomic
    def accept_request(
        *,
        request_obj: PlayerRegistrationRequest,
        accepted_by: User,
    ) -> PlayerRegistrationRequest:
        """
        Player accepts an INVITED or APPROVED request, creating the actual registration.
        """
        request_obj = PlayerRegistrationRequest.objects.select_for_update().get(pk=request_obj.pk)
        if request_obj.status not in [
            PlayerRegistrationRequest.Status.INVITED,
            PlayerRegistrationRequest.Status.APPROVED,
        ]:
            raise RequestAlreadyReviewed("This registration request cannot be accepted in its current state.")

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
        # Mark as approved since it's now effectively active
        request_obj.status = PlayerRegistrationRequest.Status.APPROVED
        request_obj.save()

        logger.info(
            "Player registration request accepted: %s by %s",
            request_obj.id,
            accepted_by.email,
        )
        publish_registration_request_event(
            PLAYER_REGISTRATION_INVITATION_ACCEPTED, request_obj, actor_id=accepted_by.id
        )
        return request_obj

    @staticmethod
    @transaction.atomic
    def decline_invitation(
        *, request_obj: PlayerRegistrationRequest, declined_by: User, review_notes: str = ""
    ) -> PlayerRegistrationRequest:
        """Decline a club invitation, atomically and exactly once."""
        request_obj = PlayerRegistrationRequest.objects.select_for_update().get(pk=request_obj.pk)
        if request_obj.status != PlayerRegistrationRequest.Status.INVITED:
            raise RequestAlreadyReviewed("This registration invitation cannot be declined in its current state.")

        request_obj.status = PlayerRegistrationRequest.Status.REJECTED
        request_obj.review_notes = review_notes
        request_obj.reviewed_by = declined_by
        request_obj.reviewed_at = timezone.now()
        request_obj.save(update_fields=["status", "review_notes", "reviewed_by", "reviewed_at", "updated_at"])
        publish_registration_request_event(
            PLAYER_REGISTRATION_INVITATION_REJECTED, request_obj, actor_id=declined_by.id
        )
        return request_obj
