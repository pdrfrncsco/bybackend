"""
BOLAYETU — Player Services

Write operations for the Players domain (global entity).

Architecture (01_CODING_STANDARDS.md):
    - Services handle all business logic and mutations.
    - Never call Services from other Services; compose at the view level.
    - Use Selectors for all reads.
"""

import logging
from datetime import date
from typing import Optional

from django.db import transaction
from django.utils.text import slugify

from players.models import Player, PlayerRegistration

logger = logging.getLogger("players")


class PlayerAlreadyExists(Exception):
    """Raised when a player with the same slug already exists."""
    pass


class PlayerNotFound(Exception):
    """Raised when a player cannot be found."""
    pass


class PlayerRegistrationConflict(Exception):
    """Raised when an active registration already exists for the same player+club+competition."""
    pass


class PlayerService:
    """
    Write operations for the global Player entity.

    Players are global — they are not owned by any tenant.
    Only platform staff (or automated processes) should create/update players.
    """

    @staticmethod
    @transaction.atomic
    def create_player(
        first_name: str,
        last_name: str,
        date_of_birth: Optional[date] = None,
        nationality: Optional[str] = None,
        primary_position: str = Player.Position.MULTIPLE,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        height_cm: Optional[int] = None,
        weight_kg: Optional[int] = None,
        foot: Optional[str] = None,
        bio: Optional[str] = None,
        avatar: Optional[str] = None,
        user_id=None,
    ) -> Player:
        """
        Create a new global Player.

        Generates a unique slug from the player's name.
        Raises PlayerAlreadyExists if slug conflicts.
        """
        base_slug = slugify(f"{first_name} {last_name}")
        slug = base_slug
        counter = 1

        while Player.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        player = Player.objects.create(
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            slug=slug,
            date_of_birth=date_of_birth,
            nationality=nationality,
            primary_position=primary_position,
            email=email or None,
            phone=phone or None,
            height_cm=height_cm,
            weight_kg=weight_kg,
            foot=foot or None,
            bio=bio or None,
            avatar=avatar or None,
            user_id=user_id,
        )

        logger.info("Player created: %s (id=%s)", player.full_name, player.id)
        return player

    @staticmethod
    @transaction.atomic
    def update_player(player: Player, **kwargs) -> Player:
        """
        Update player profile fields.

        Only updates fields that are explicitly provided.
        """
        allowed_fields = {
            "first_name", "last_name", "date_of_birth", "nationality",
            "primary_position", "email", "phone", "height_cm", "weight_kg",
            "foot", "bio", "avatar", "status",
        }
        updated = []
        for field, value in kwargs.items():
            if field in allowed_fields:
                setattr(player, field, value)
                updated.append(field)

        if updated:
            player.save(update_fields=updated)
            logger.info("Player updated: %s — fields: %s", player.full_name, updated)

        return player

    @staticmethod
    @transaction.atomic
    def retire_player(player: Player) -> Player:
        """Mark a player as retired."""
        player.status = Player.PlayerStatus.RETIRED
        player.save(update_fields=["status"])
        logger.info("Player retired: %s", player.full_name)
        return player


class PlayerRegistrationService:
    """
    Write operations for PlayerRegistration (tenant-scoped).

    Registrations are managed by tenant staff (club managers/admins).
    """

    @staticmethod
    @transaction.atomic
    def register_player(
        player: Player,
        club,
        tenant,
        joined_date: date,
        shirt_number: Optional[int] = None,
        competition=None,
    ) -> PlayerRegistration:
        """
        Register a player with a club for an optional competition.

        Raises PlayerRegistrationConflict if an active registration already
        exists for this player + club + competition combination.
        """
        # Check for existing active registration
        conflict_qs = PlayerRegistration.objects.filter(
            player=player,
            club=club,
            competition=competition,
            status__in=[
                PlayerRegistration.RegistrationStatus.REGISTERED,
                PlayerRegistration.RegistrationStatus.LOANED,
            ],
        )
        if conflict_qs.exists():
            raise PlayerRegistrationConflict(
                f"{player.full_name} is already actively registered at {club.name}."
            )

        registration = PlayerRegistration.objects.create(
            player=player,
            club=club,
            tenant=tenant,
            competition=competition,
            joined_date=joined_date,
            shirt_number=shirt_number,
            status=PlayerRegistration.RegistrationStatus.REGISTERED,
        )

        logger.info(
            "Player registered: %s → %s (id=%s)",
            player.full_name, club.name, registration.id
        )
        return registration

    @staticmethod
    @transaction.atomic
    def transfer_player(
        registration: PlayerRegistration,
        left_date: Optional[date] = None,
    ) -> PlayerRegistration:
        """
        Mark a player registration as transferred (ended).

        Call this before creating a new registration at another club.
        """
        registration.deactivate(left_date=left_date)
        logger.info(
            "Player transferred: %s left %s",
            registration.player.full_name, registration.club.name
        )
        return registration

    @staticmethod
    @transaction.atomic
    def update_stats(
        registration: PlayerRegistration,
        matches_played: Optional[int] = None,
        goals: Optional[int] = None,
        assists: Optional[int] = None,
        yellow_cards: Optional[int] = None,
        red_cards: Optional[int] = None,
    ) -> PlayerRegistration:
        """
        Update per-registration stats and propagate totals to the global Player.

        This is called after each match is processed (Match Center integration).
        """
        fields_updated = []
        if matches_played is not None:
            registration.matches_played = matches_played
            fields_updated.append("matches_played")
        if goals is not None:
            registration.goals = goals
            fields_updated.append("goals")
        if assists is not None:
            registration.assists = assists
            fields_updated.append("assists")
        if yellow_cards is not None:
            registration.yellow_cards = yellow_cards
            fields_updated.append("yellow_cards")
        if red_cards is not None:
            registration.red_cards = red_cards
            fields_updated.append("red_cards")

        if fields_updated:
            registration.save(update_fields=fields_updated)

        # Recalculate global totals on the Player
        player = registration.player
        totals = PlayerRegistration.objects.filter(player=player).aggregate(
            total_matches=__import__("django.db.models", fromlist=["Sum"]).Sum("matches_played"),
            total_goals=__import__("django.db.models", fromlist=["Sum"]).Sum("goals"),
            total_assists=__import__("django.db.models", fromlist=["Sum"]).Sum("assists"),
        )
        player.total_matches = totals["total_matches"] or 0
        player.total_goals = totals["total_goals"] or 0
        player.total_assists = totals["total_assists"] or 0
        player.save(update_fields=["total_matches", "total_goals", "total_assists"])

        return registration
