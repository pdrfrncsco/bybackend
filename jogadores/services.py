"""
BOLAYETU — Jogadores Service Layer
Skills: BOLAYETU_ARCHITECTURE, BOLAYETU_BACKEND_SKILL, BOLAYETU_MULTITENANT_SKILL
"""

from django.db import IntegrityError
from rest_framework.exceptions import ValidationError

from common.base import BaseService
from .models import Player, PlayerHistory


class PlayerService(BaseService):
    """
    Service layer for mutating Player and PlayerHistory.
    """

    @BaseService.atomic
    def create_player(self, *, data: dict) -> Player:
        """
        Creates a new player under the current tenant context.
        """
        self._assert_tenant()
        
        # Extract nested history data
        history_data = data.pop('history', [])
        
        player = Player(tenant=self.tenant)
        
        allowed_fields = {f.name for f in player._meta.fields} - {'id', 'tenant', 'created_at', 'updated_at'}
        for field, value in data.items():
            if field in allowed_fields:
                setattr(player, field, value)

        try:
            player.full_clean()
            player.save()
            
            if history_data:
                PlayerHistory.objects.bulk_create(
                    [PlayerHistory(player=player, **row) for row in history_data]
                )
        except IntegrityError:
            raise ValidationError({"number": "Já existe um jogador com este número neste clube."})
            
        return player

    @BaseService.atomic
    def update_player(self, *, player: Player, data: dict) -> Player:
        """
        Updates an existing player.
        """
        self._assert_tenant()
        if player.tenant != self.tenant:
            from common.exceptions import PermissionDeniedException
            raise PermissionDeniedException("You cannot edit a player belonging to another tenant.")

        # Extract nested history data
        history_data = data.pop('history', None)

        allowed_fields = {f.name for f in player._meta.fields} - {'id', 'tenant', 'created_at', 'updated_at'}
        for field, value in data.items():
            if field in allowed_fields:
                setattr(player, field, value)

        try:
            player.full_clean()
            player.save()
            
            if history_data is not None:
                player.history.all().delete()
                if history_data:
                    PlayerHistory.objects.bulk_create(
                        [PlayerHistory(player=player, **row) for row in history_data]
                    )
        except IntegrityError:
            raise ValidationError({"number": "Já existe um jogador com este número neste clube."})
            
        return player

    @BaseService.atomic
    def delete_player(self, *, player: Player) -> None:
        """
        Deletes a player.
        """
        self._assert_tenant()
        if player.tenant != self.tenant:
            from common.exceptions import PermissionDeniedException
            raise PermissionDeniedException("You cannot delete a player belonging to another tenant.")
            
        player.delete()

    @BaseService.atomic
    def create_player_history(self, *, data: dict) -> PlayerHistory:
        """
        Creates a PlayerHistory entry.
        """
        self._assert_tenant()
        
        player = data.get('player')
        if player is None or player.tenant != self.tenant:
            raise ValidationError({"player": "Jogador inválido ou não pertence a este tenant."})
            
        history = PlayerHistory()
        for field, value in data.items():
            if hasattr(history, field) and field not in ['id', 'created_at', 'updated_at']:
                setattr(history, field, value)
                
        history.full_clean()
        history.save()
        return history

    @BaseService.atomic
    def update_player_history(self, *, history: PlayerHistory, data: dict) -> PlayerHistory:
        """
        Updates a PlayerHistory entry.
        """
        self._assert_tenant()
        if history.player.tenant != self.tenant:
            from common.exceptions import PermissionDeniedException
            raise PermissionDeniedException("You cannot edit history for a player of another tenant.")
            
        for field, value in data.items():
            if hasattr(history, field) and field not in ['id', 'player', 'created_at', 'updated_at']:
                setattr(history, field, value)
                
        history.full_clean()
        history.save()
        return history

    @BaseService.atomic
    def delete_player_history(self, *, history: PlayerHistory) -> None:
        """
        Deletes a PlayerHistory entry.
        """
        self._assert_tenant()
        if history.player.tenant != self.tenant:
            from common.exceptions import PermissionDeniedException
            raise PermissionDeniedException("You cannot delete history for a player of another tenant.")
            
        history.delete()
