from typing import Optional
from django.utils import timezone
from django.db import transaction

from players.models import Player, PlayerOnboardingStatus


class PlayerOnboardingService:
    STEPS = [
        "account",
        "identity",
        "personal",
        "football",
        "contact",
        "guardian",
        "documents",
        "club",
        "review",
    ]

    @staticmethod
    def get_status(player: Player) -> PlayerOnboardingStatus:
        status, created = PlayerOnboardingStatus.objects.get_or_create(player=player)
        return status

    @staticmethod
    @transaction.atomic
    def complete_step(player: Player, step: str) -> PlayerOnboardingStatus:
        status = PlayerOnboardingService.get_status(player)
        field = f"{step}_complete"
        if not hasattr(status, field):
            raise ValueError("Unknown onboarding step")
        setattr(status, field, True)
        # advance current_step
        next_step = status.get_next_step()
        if next_step:
            status.current_step = next_step
        else:
            status.current_step = step
            status.completed_at = timezone.now()
        status.save()
        return status

    @staticmethod
    def is_complete(player: Player) -> bool:
        status = PlayerOnboardingService.get_status(player)
        return status.is_complete

    @staticmethod
    def progress(player: Player) -> int:
        status = PlayerOnboardingService.get_status(player)
        return status.progress_percentage
