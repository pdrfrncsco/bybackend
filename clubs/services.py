"""
BOLAYETU — Clubs Service Layer
Skills: BOLAYETU_ARCHITECTURE, BOLAYETU_BACKEND_SKILL, BOLAYETU_MULTITENANT_SKILL
"""

from common.base import BaseService
from .models import Club, Staff


class ClubService(BaseService):
    """
    Service layer for mutating Club and Staff entities.
    """

    @BaseService.atomic
    def create_club(self, *, data: dict) -> Club:
        """
        Creates a new club under the current tenant context.
        """
        self._assert_tenant()
        
        club = Club(tenant=self.tenant)
        
        for field, value in data.items():
            if hasattr(club, field) and field not in ['id', 'tenant', 'created_at', 'updated_at']:
                setattr(club, field, value)
                
        club.full_clean()
        club.save()
        return club

    @BaseService.atomic
    def update_club(self, *, club: Club, data: dict) -> Club:
        """
        Updates an existing club ensuring it belongs to the current tenant.
        """
        self._assert_tenant()
        if club.tenant != self.tenant:
            from common.exceptions import PermissionDeniedException
            raise PermissionDeniedException("You cannot edit a club belonging to another tenant.")

        for field, value in data.items():
            if hasattr(club, field) and field not in ['id', 'tenant', 'created_at', 'updated_at']:
                setattr(club, field, value)

        club.full_clean()
        club.save()
        return club

    @BaseService.atomic
    def delete_club(self, *, club: Club) -> None:
        """
        Removes a club.
        """
        self._assert_tenant()
        if club.tenant != self.tenant:
            from common.exceptions import PermissionDeniedException
            raise PermissionDeniedException("You cannot delete a club belonging to another tenant.")
            
        club.delete()

    @BaseService.atomic
    def create_staff(self, *, data: dict) -> Staff:
        """
        Creates a new staff member.
        """
        self._assert_tenant()
        
        # Verify club belongs to this tenant if provided
        club_id = data.get('club') or data.get('club_id')
        if club_id:
            club = Club.objects.filter(tenant=self.tenant).get(id=club_id)
            data['club'] = club

        staff = Staff(tenant=self.tenant)
        
        for field, value in data.items():
            if hasattr(staff, field) and field not in ['id', 'tenant', 'created_at', 'updated_at']:
                setattr(staff, field, value)

        staff.full_clean()
        staff.save()
        return staff

    @BaseService.atomic
    def update_staff(self, *, staff: Staff, data: dict) -> Staff:
        """
        Updates a staff member.
        """
        self._assert_tenant()
        if staff.tenant != self.tenant:
            from common.exceptions import PermissionDeniedException
            raise PermissionDeniedException("You cannot edit a staff member belonging to another tenant.")

        # Verify club belongs to this tenant if provided
        if 'club' in data or 'club_id' in data:
            club_id = data.get('club') or data.get('club_id')
            if club_id:
                club = Club.objects.filter(tenant=self.tenant).get(id=club_id)
                data['club'] = club

        for field, value in data.items():
            if hasattr(staff, field) and field not in ['id', 'tenant', 'created_at', 'updated_at']:
                setattr(staff, field, value)

        staff.full_clean()
        staff.save()
        return staff

    @BaseService.atomic
    def delete_staff(self, *, staff: Staff) -> None:
        """
        Deletes a staff member.
        """
        self._assert_tenant()
        if staff.tenant != self.tenant:
            from common.exceptions import PermissionDeniedException
            raise PermissionDeniedException("You cannot delete staff belonging to another tenant.")
            
        staff.delete()
