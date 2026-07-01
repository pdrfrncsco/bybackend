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
    def list_all_active() -> list[Competition]:
        """Public selector: all competitions, ordered by most recent."""
        return list(
            Competition.objects.select_related("tenant").order_by("-created_at")
        )

    @staticmethod
    def get_by_id(*, tenant: Tenant, competition_id) -> Competition | None:
        try:
            return Competition.objects.get(id=competition_id, tenant=tenant)
        except Competition.DoesNotExist:
            return None

    @staticmethod
    def get_by_id_public(*, competition_id) -> Competition | None:
        """Public selector: get a competition by ID without tenant guard."""
        try:
            return Competition.objects.select_related("tenant").get(id=competition_id)
        except Competition.DoesNotExist:
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
    def list_by_competition(*, tenant: Tenant, competition_id) -> QuerySet:
        """List all matches in a competition, ordered by round and date."""
        return Match.objects.filter(
            competition_id=competition_id,
            tenant=tenant
        ).select_related("home_club", "away_club").order_by("round_number", "match_date")

    @staticmethod
    def list_by_club(*, tenant: Tenant, club_id) -> QuerySet:
        """List matches involving a specific club (home or away)."""
        return Match.objects.filter(
            Q(home_club_id=club_id) | Q(away_club_id=club_id),
            tenant=tenant
        ).select_related("home_club", "away_club", "competition").order_by("match_date")


class StandingSelector:
    @staticmethod
    def list_by_competition(*, tenant: Tenant, competition_id) -> QuerySet:
        """List league table standing rows sorted by position."""
        return Standing.objects.filter(
            competition_id=competition_id,
            tenant=tenant
        ).select_related("club").order_by("position", "-points", "-goal_difference", "-goals_for")

