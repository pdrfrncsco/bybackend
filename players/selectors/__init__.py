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
    def list_active() -> QuerySet:
        """List all active players."""
        return Player.objects.filter(status="active").order_by("-updated_at")
    
    @staticmethod
    def search(query: str) -> QuerySet:
        """Search players by name."""
        return Player.objects.filter(
            Q(first_name__icontains=query) | Q(last_name__icontains=query)
        ).filter(status="active")
    
    @staticmethod
    def list_by_position(position: str) -> QuerySet:
        """List players by primary position."""
        return Player.objects.filter(
            primary_position=position,
            status="active"
        )
    
    @staticmethod
    def list_by_nationality(nationality: str) -> QuerySet:
        """List players by nationality."""
        return Player.objects.filter(
            nationality=nationality,
            status="active"
        )


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
        """List a player's entire career history."""
        return PlayerRegistration.objects.filter(
            player_id=player_id
        ).select_related("club", "competition").order_by("-joined_date")
