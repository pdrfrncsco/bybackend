"""
BOLAYETU — Clubes Selector Layer
Skills: BOLAYETU_ARCHITECTURE, BOLAYETU_BACKEND_SKILL, BOLAYETU_MULTITENANT_SKILL
"""

from django.db.models import QuerySet
from common.base import BaseSelector
from .models import Club, ClubHistory, Staff


class ClubSelector(BaseSelector):
    """
    Selector layer for retrieving Club, ClubHistory, and Staff details.
    """

    def list_clubs(self, *, search_query: str = None) -> QuerySet:
        """
        List clubs, scoped by tenant.
        """
        # Starting with tenant-isolated queryset via self._base_qs
        qs = self._base_qs(Club).select_related('tenant')
        
        if search_query:
            from django.db.models import Q
            qs = qs.filter(
                Q(name__icontains=search_query) |
                Q(location__icontains=search_query) |
                Q(stadium_name__icontains=search_query)
            )
        return qs

    def get_club_detail(self, club_id: str) -> Club:
        """
        Retrieve details of a specific club, enforcing tenant isolation.
        """
        return self._base_qs(Club).prefetch_related('history', 'staff_members').get(id=club_id)

    def list_club_history(self, *, search_query: str = None) -> QuerySet:
        """
        Retrieve historical placements for all clubs of this tenant.
        """
        self._assert_tenant()
        qs = ClubHistory.objects.filter(club__tenant=self.tenant).select_related('club')
        
        if search_query:
            from django.db.models import Q
            qs = qs.filter(
                Q(club__name__icontains=search_query) |
                Q(season__icontains=search_query) |
                Q(tournament_name__icontains=search_query) |
                Q(placement__icontains=search_query)
            )
        return qs.order_by('-season', 'id')

    def list_staff(self, *, club_id: str = None, search_query: str = None) -> QuerySet:
        """
        Retrieve staff members scoped to tenant, optionally filtered by club.
        """
        qs = self._base_qs(Staff).select_related('club')
        
        if club_id:
            qs = qs.filter(club_id=club_id)
            
        if search_query:
            from django.db.models import Q
            qs = qs.filter(
                Q(name__icontains=search_query) |
                Q(role__icontains=search_query) |
                Q(club__name__icontains=search_query)
            )
        return qs
