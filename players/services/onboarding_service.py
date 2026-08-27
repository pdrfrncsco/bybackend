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
        "club",
        "review",
    ]

    @staticmethod
    def get_status(player: Player) -> PlayerOnboardingStatus:
        status, created = PlayerOnboardingStatus.objects.get_or_create(
            player=player,
            defaults={"account_complete": True, "current_step": "personal"},
        )
        if not status.account_complete:
            status.account_complete = True
            status.save(update_fields=["account_complete"])
        return status

    @staticmethod
    @transaction.atomic
    def complete_step(player: Player, step: str) -> PlayerOnboardingStatus:
        status = PlayerOnboardingService.get_status(player)
        if step == "profile":
            step = "personal"
        if step == "documents":
            raise ValueError("Documents are not part of player onboarding")
        field = f"{step}_complete"
        if not hasattr(status, field):
            raise ValueError("Unknown onboarding step")
        setattr(status, field, True)
        if not status.account_complete:
            status.account_complete = True
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
