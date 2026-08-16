"""
BOLAYETU — Player Selectors

Read-only selectors for players and related entities. Improvements added:
- get_by_global_id, get_with_profile_photo, prefetch/select_related optimizations
- Invite/Career/Statistics selectors
- Tenant-aware current registration and optional eager-loading flags
"""

from typing import Optional
from django.db.models import QuerySet, Q

from players.models import Player, PlayerRegistration


class PlayerSelector:
    """Read-only queries for Player data."""

    @staticmethod
    def get_by_id(player_id) -> Optional[Player]:
        try:
            return Player.objects.get(id=player_id)
        except Player.DoesNotExist:
            return None

    @staticmethod
    def get_by_global_id(global_id: str) -> Optional[Player]:
        """Fetch by global_id (useful when integrating external systems)."""
        try:
            return Player.objects.get(global_id=global_id)
        except Player.DoesNotExist:
            return None

    @staticmethod
    def get_by_slug(slug: str) -> Optional[Player]:
        try:
            return Player.objects.get(slug=slug)
        except Player.DoesNotExist:
            return None

    @staticmethod
    def get_public_by_slug(slug: str) -> Optional[Player]:
        try:
            return Player.objects.get(slug=slug, status=Player.PlayerStatus.ACTIVE, is_public=True)
        except Player.DoesNotExist:
            return None

    @staticmethod
    def get_with_profile_photo(player_id, prefetch_related: bool = False) -> Optional[Player]:
        """Get player with profile_photo relation pre-selected to avoid N+1."""
        qs = Player.objects
        if prefetch_related:
            qs = qs.select_related("profile_photo")
        try:
            return qs.get(id=player_id)
        except Player.DoesNotExist:
            return None

    @staticmethod
    def list_active(limit: int = 100) -> QuerySet:
        return Player.objects.filter(status=Player.PlayerStatus.ACTIVE, is_public=True).order_by("-updated_at")[:limit]

    @staticmethod
    def list_players(
        *,
        search: Optional[str] = None,
        position: Optional[str] = None,
        nationality: Optional[str] = None,
        without_club: bool = False,
        include_football_profile: bool = False,
    ) -> QuerySet:
        qs = Player.objects.filter(status=Player.PlayerStatus.ACTIVE, is_public=True)
        if search:
            qs = qs.filter(
                Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(slug__icontains=search)
            )
        if position:
            qs = qs.filter(primary_position=position)
        if nationality:
            qs = qs.filter(nationality=nationality)
        if without_club:
            qs = qs.exclude(registrations__status__in=[PlayerRegistration.RegistrationStatus.REGISTERED, PlayerRegistration.RegistrationStatus.LOANED])
        if include_football_profile:
            qs = qs.select_related("football_profile")
        return qs.order_by("-updated_at")

    @staticmethod
    def search(query: str, without_club: bool = False) -> QuerySet:
        qs = Player.objects.filter(
            Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(slug__icontains=query)
        ).filter(status=Player.PlayerStatus.ACTIVE, is_public=True)
        if without_club:
            qs = qs.exclude(registrations__status__in=[PlayerRegistration.RegistrationStatus.REGISTERED, PlayerRegistration.RegistrationStatus.LOANED])
        return qs

    @staticmethod
    def list_by_position(position: str) -> QuerySet:
        """Backward-compatible helper for listing by position."""
        return PlayerSelector.list_players(position=position)

    @staticmethod
    def list_by_nationality(nationality: str) -> QuerySet:
        """Backward-compatible helper for listing by nationality."""
        return PlayerSelector.list_players(nationality=nationality)

    @staticmethod
    def get_for_user(user) -> Optional[Player]:
        if not user or not getattr(user, "is_authenticated", False):
            return None
        # Prefer explicit reverse relation if available
        player = getattr(user, "player_profile", None)
        if player:
            return player
        # Fallback: try to query by user_id if Player has user_id field
        try:
            return Player.objects.get(user_id=getattr(user, "id", None))
        except Exception:
            return None


class PlayerRegistrationSelector:
    """Read-only queries for PlayerRegistration data. Tenant-aware where appropriate."""

    @staticmethod
    def get_current_registration(player_id, tenant_id: Optional[str] = None) -> Optional[PlayerRegistration]:
        qs = PlayerRegistration.objects.filter(player_id=player_id, status__in=[PlayerRegistration.RegistrationStatus.REGISTERED, PlayerRegistration.RegistrationStatus.LOANED])
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        return qs.select_related("club", "competition").first()

    @staticmethod
    def list_by_club(club_id, include_player=False) -> QuerySet:
        qs = PlayerRegistration.objects.filter(club_id=club_id, status__in=[PlayerRegistration.RegistrationStatus.REGISTERED, PlayerRegistration.RegistrationStatus.LOANED])
        if include_player:
            qs = qs.select_related("player")
        return qs.order_by("player__last_name", "player__first_name")

    @staticmethod
    def list_by_competition(competition_id) -> QuerySet:
        return PlayerRegistration.objects.filter(competition_id=competition_id, status=PlayerRegistration.RegistrationStatus.REGISTERED).select_related("player", "club").order_by("joined_date")

    @staticmethod
    def list_career(player_id) -> QuerySet:
        return PlayerRegistration.objects.filter(player_id=player_id).select_related("club", "competition").order_by("-joined_date")

    @staticmethod
    def get_career_entries(player_id):
        try:
            from players.models import PlayerCareer
            return PlayerCareer.objects.filter(player_id=player_id).select_related("club", "competition").order_by("-season", "-appearances")
        except Exception:
            return PlayerRegistration.objects.filter(player_id=player_id).select_related("club", "competition").order_by("-joined_date")

    @staticmethod
    def get_season_statistics(player_id):
        try:
            from players.models import PlayerSeasonStatistics
            return PlayerSeasonStatistics.objects.filter(player_id=player_id).select_related("club", "competition").order_by("-season")
        except Exception:
            return PlayerRegistration.objects.none()


class PlayerInviteSelector:
    """Selectors for PlayerInvite model."""

    @staticmethod
    def get_by_token(token: str):
        try:
            from players.models import PlayerInvite
            return PlayerInvite.objects.get(token=token)
        except Exception:
            return None

    @staticmethod
    def list_by_club(club_id) -> QuerySet:
        try:
            from players.models import PlayerInvite
            return PlayerInvite.objects.filter(club_id=club_id).order_by("-created_at")
        except Exception:
            return PlayerRegistration.objects.none()


class PlayerCareerSelector:
    """Selectors for PlayerCareer model."""

    @staticmethod
    def list_for_player(player_id) -> QuerySet:
        try:
            from players.models import PlayerCareer
            return PlayerCareer.objects.filter(player_id=player_id).select_related("club", "competition").order_by("-season")
        except Exception:
            return PlayerRegistration.objects.filter(player_id=player_id).select_related("club", "competition").order_by("-joined_date")


class PlayerSeasonStatisticsSelector:
    """Selectors for PlayerSeasonStatistics."""

    @staticmethod
    def get_for_player(player_id) -> QuerySet:
        try:
            from players.models import PlayerSeasonStatistics
            return PlayerSeasonStatistics.objects.filter(player_id=player_id).select_related("club", "competition").order_by("-season")
        except Exception:
            return PlayerRegistration.objects.none()
