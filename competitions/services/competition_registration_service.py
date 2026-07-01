"""
BOLAYETU — CompetitionRegistrationService

Handles business logic for registering clubs in competitions.
"""

import logging
from django.db import transaction

from core.models import Tenant
from clubs.models import Club
from competitions.models import Competition, CompetitionRegistration, Standing
from competitions.exceptions import CompetitionNotFound

logger = logging.getLogger("competitions")


class ClubAlreadyRegistered(Exception):
    """Raised when a club is already registered in the competition."""
    pass


class CompetitionRegistrationService:
    """
    Handles registering clubs into competitions and initializing their standings.
    """

    @staticmethod
    @transaction.atomic
    def register_club(
        *,
        tenant: Tenant,
        competition: Competition,
        club: Club,
    ) -> CompetitionRegistration:
        """
        Registers a club in a competition.
        Also creates an initial Standing record for the club.
        """
        # Ensure club and competition belong to the same tenant
        if club.tenant != tenant or competition.tenant != tenant:
            raise PermissionError("Club and Competition must belong to the same tenant organization.")

        # Check if already registered
        if CompetitionRegistration.objects.filter(competition=competition, club=club).exists():
            raise ClubAlreadyRegistered(f"Club {club.name} is already registered in {competition.name}.")

        # Create registration
        registration = CompetitionRegistration.objects.create(
            competition=competition,
            club=club,
            tenant=tenant,
        )

        # Create initial Standing record
        # Posicao default = 1, will be updated when recalculating
        Standing.objects.get_or_create(
            competition=competition,
            club=club,
            tenant=tenant,
            defaults={
                "played": 0,
                "won": 0,
                "drawn": 0,
                "lost": 0,
                "goals_for": 0,
                "goals_against": 0,
                "goal_difference": 0,
                "points": 0,
                "position": 1,
            }
        )

        logger.info(
            "Club %s registered in Competition %s (tenant=%s)",
            club.name, competition.name, tenant.slug
        )
        return registration

    @staticmethod
    @transaction.atomic
    def unregister_club(
        *,
        tenant: Tenant,
        competition: Competition,
        club: Club,
    ) -> None:
        """
        Unregisters a club from a competition.
        Also deletes their Standing record.
        """
        reg = CompetitionRegistration.objects.filter(competition=competition, club=club, tenant=tenant)
        if not reg.exists():
            return

        reg.delete()
        Standing.objects.filter(competition=competition, club=club, tenant=tenant).delete()
        logger.info(
            "Club %s unregistered from Competition %s (tenant=%s)",
            club.name, competition.name, tenant.slug
        )
