"""
BOLAYETU — Player Selectors

Read-only query methods for players.
"""

from typing import Optional
from django.db.models import QuerySet, Q

from players.models import Player, PlayerRegistration


class PlayerSelector:
    """Read-only queries for Player data."""
    
    @staticmethod
    def get_by_id(player_id) -> Optional[Player]:
        """Get a player by ID."""
        try:
            return Player.objects.get(id=player_id)
        except Player.DoesNotExist:
            return None
    
    @staticmethod
    def get_by_slug(slug: str) -> Optional[Player]:
        """Get a player by slug (URL-safe identifier)."""
        try:
            return Player.objects.get(slug=slug)
        except Player.DoesNotExist:
            return None

    @staticmethod
    def get_public_by_slug(slug: str) -> Optional[Player]:
        """Get a public active player by slug."""
        try:
            return Player.objects.get(slug=slug, status="active", is_public=True)
        except Player.DoesNotExist:
            return None
    
    @staticmethod
    def list_active() -> QuerySet:
        """List all active players."""
        return Player.objects.filter(status="active", is_public=True).order_by("-updated_at")

    @staticmethod
    def list_public_active() -> QuerySet:
        """List all public active players."""
        return Player.objects.filter(status="active", is_public=True).order_by("-updated_at")

    @staticmethod
    def list_players(
        *,
        position: Optional[str] = None,
        nationality: Optional[str] = None,
        without_club: bool = False,
    ) -> QuerySet:
        """List active public players with optional filters."""
        qs = Player.objects.filter(status="active", is_public=True)
        if position:
            qs = qs.filter(primary_position=position)
        if nationality:
            qs = qs.filter(nationality=nationality)
        if without_club:
            qs = qs.exclude(
                registrations__status__in=["registered", "loaned"]
            )
        return qs.order_by("-updated_at")

    @staticmethod
    def search(query: str, without_club: bool = False) -> QuerySet:
        """Search players by name."""
        qs = Player.objects.filter(
            Q(first_name__icontains=query) | Q(last_name__icontains=query)
        ).filter(status="active", is_public=True)
        if without_club:
            qs = qs.exclude(
                registrations__status__in=["registered", "loaned"]
            )
        return qs

    @staticmethod
    def list_by_position(position: str) -> QuerySet:
        """List players by primary position."""
        return Player.objects.filter(
            primary_position=position,
            status="active",
            is_public=True,
        )

    @staticmethod
    def list_by_nationality(nationality: str) -> QuerySet:
        """List players by nationality."""
        return Player.objects.filter(
            nationality=nationality,
            status="active",
            is_public=True,
        )

    @staticmethod
    def get_for_user(user) -> Optional[Player]:
        """Get the player profile linked to an authenticated user."""
        if not user or not getattr(user, "is_authenticated", False):
            return None
        try:
            return user.player_profile
        except Player.DoesNotExist:
            return None


class PlayerRegistrationSelector:
    """Read-only queries for PlayerRegistration data."""
    
    @staticmethod
    def get_current_registration(player_id) -> Optional[PlayerRegistration]:
        """Get player's current registration (if any)."""
        return PlayerRegistration.objects.filter(
            player_id=player_id,
            status__in=["registered", "loaned"]
        ).select_related("club", "competition").first()
    
    @staticmethod
    def list_by_club(club_id) -> QuerySet:
        """List all active player registrations for a club."""
        return PlayerRegistration.objects.filter(
            club_id=club_id,
            status__in=["registered", "loaned"]
        ).select_related("player").order_by("player__last_name", "player__first_name")
    
    @staticmethod
    def list_by_competition(competition_id) -> QuerySet:
        """List all players registered in a competition."""
        return PlayerRegistration.objects.filter(
            competition_id=competition_id,
            status="registered"
        ).select_related("player", "club").order_by("joined_date")
    
    @staticmethod
    def list_career(player_id) -> QuerySet:
        """List a player's entire career history (registrations)."""
        return PlayerRegistration.objects.filter(
            player_id=player_id
        ).select_related("club", "competition").order_by("-joined_date")

    @staticmethod
    def get_career_entries(player_id):
        """Return PlayerCareer entries for a player, if the model exists."""
        try:
            from players.models import PlayerCareer
            return PlayerCareer.objects.filter(player_id=player_id).select_related("club", "competition").order_by("-season", "-appearances")
        except Exception:
            # If PlayerCareer model/migration not applied, fall back to registrations
            return PlayerRegistration.objects.filter(player_id=player_id).select_related("club", "competition").order_by("-joined_date")

    @staticmethod
    def get_season_statistics(player_id):
        """Return season statistics for a player (PlayerSeasonStatistics if available)."""
        try:
            from players.models import PlayerSeasonStatistics
            return PlayerSeasonStatistics.objects.filter(player_id=player_id).select_related("club", "competition").order_by("-season")
        except Exception:
            # If not available, return empty queryset from PlayerRegistration for compatibility
            return PlayerRegistration.objects.none()
