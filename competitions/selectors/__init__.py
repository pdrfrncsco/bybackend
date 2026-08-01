from django.db.models import QuerySet, Q
from core.models import Tenant
from competitions.models import Competition, CompetitionRegistration, Match, Standing


class CompetitionSelector:
    @staticmethod
    def list_for_tenant(*, tenant: Tenant) -> list[Competition]:
        return list(
            Competition.objects.filter(tenant=tenant).order_by("-created_at")
        )

    @staticmethod
    def list_all_active(*, tenant: Tenant | None = None) -> list[Competition]:
        """Public selector: competitions ordered by most recent."""
        queryset = Competition.objects.select_related("tenant")
        if tenant is not None:
            queryset = queryset.filter(tenant=tenant)
        return list(queryset.order_by("-created_at"))

    @staticmethod
    def get_by_id(*, tenant: Tenant, competition_id) -> Competition | None:
        try:
            return Competition.objects.get(id=competition_id, tenant=tenant)
        except Competition.DoesNotExist:
            return None

    @staticmethod
    def get_by_id_public(*, competition_id, tenant: Tenant | None = None) -> Competition | None:
        """
        Public selector: get a competition by ID (UUID string) or slug.
        
        Args:
            competition_id: Either a UUID string (e.g., "a1b2c3d4-...") or a slug (e.g., "cup-2026")
            tenant: Optional tenant filter for scoped queries
            
        Returns:
            Competition instance or None if not found
        """
        try:
            queryset = Competition.objects.select_related("tenant")
            if tenant is not None:
                queryset = queryset.filter(tenant=tenant)
            
            # Try slug first (most common case)
            try:
                return queryset.get(slug=competition_id)
            except Competition.DoesNotExist:
                pass
            
            # If slug not found, try as UUID
            # Django's UUIDField handles UUID string conversion automatically
            try:
                return queryset.get(id=competition_id)
            except (Competition.DoesNotExist, ValueError):
                # ValueError raised if competition_id is not a valid UUID string
                return None
                
        except Exception:
            return None

class CompetitionRegistrationSelector:
    @staticmethod
    def list_by_competition(*, tenant: Tenant, competition_id) -> QuerySet:
        """List all club registrations for a specific competition."""
        return CompetitionRegistration.objects.filter(
            competition_id=competition_id,
            tenant=tenant
        ).select_related("club")

    @staticmethod
    def list_by_club(*, tenant: Tenant, club_id) -> QuerySet:
        """List all competition registrations for a specific club."""
        return CompetitionRegistration.objects.filter(
            club_id=club_id,
            tenant=tenant
        ).select_related("competition")


class MatchSelector:
    @staticmethod
    def get_by_id(*, tenant: Tenant, match_id) -> Match | None:
        try:
            return Match.objects.select_related("home_club", "away_club", "competition").get(id=match_id, tenant=tenant)
        except Match.DoesNotExist:
            return None

    @staticmethod
    def list_by_competition(
        *,
        tenant: Tenant,
        competition_id,
        group_id: str | None = None,
        phase: str | None = None,
    ) -> QuerySet:
        """List all matches in a competition, ordered by round and date."""
        queryset = Match.objects.filter(
            competition_id=competition_id,
            tenant=tenant
        ).select_related("home_club", "away_club")
        if group_id is not None:
            queryset = queryset.filter(group_id=group_id)
        if phase is not None:
            queryset = queryset.filter(phase=phase)
        return queryset.order_by("phase", "group_id", "round_number", "match_date")

    @staticmethod
    def list_by_club(*, tenant: Tenant, club_id) -> QuerySet:
        """List matches involving a specific club (home or away)."""
        return Match.objects.filter(
            Q(home_club_id=club_id) | Q(away_club_id=club_id),
            tenant=tenant
        ).select_related("home_club", "away_club", "competition").order_by("match_date")


class StandingSelector:
    @staticmethod
    def list_by_competition(
        *,
        tenant: Tenant,
        competition_id,
        group_id: str | None = None,
        phase: str | None = None,
    ) -> QuerySet:
        """List league table standing rows sorted by position."""
        queryset = Standing.objects.filter(
            competition_id=competition_id,
            tenant=tenant
        ).select_related("club")
        if group_id is not None:
            queryset = queryset.filter(group_id=group_id)
        if phase is not None:
            queryset = queryset.filter(phase=phase)
        return queryset.order_by("phase", "group_id", "position", "-points", "-goal_difference", "-goals_for")

