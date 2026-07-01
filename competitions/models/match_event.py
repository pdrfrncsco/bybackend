"""
BOLAYETU — MatchEvent Model (Phase 4: Match Center)

Represents individual in-game events: goals, cards, substitutions.
Linked to a Match, Player, and Club. Tenant-scoped.
"""

from django.db import models
from common.models import BaseModel


class MatchEvent(BaseModel):
    """
    An in-game event within a match (goal, yellow card, red card, substitution).

    Goals auto-derive the match score when recalculated via MatchService.
    """

    class EventType(models.TextChoices):
        GOAL = "goal", "Golo"
        OWN_GOAL = "own_goal", "Golo Contra"
        YELLOW_CARD = "yellow_card", "Cartão Amarelo"
        RED_CARD = "red_card", "Cartão Vermelho"
        YELLOW_RED = "yellow_red", "Segundo Amarelo / Vermelho"
        SUBSTITUTION_IN = "substitution_in", "Substituição (Entra)"
        SUBSTITUTION_OUT = "substitution_out", "Substituição (Sai)"
        PENALTY_SCORED = "penalty_scored", "Penálti Marcado"
        PENALTY_MISSED = "penalty_missed", "Penálti Falhado"

    # Goals + own goals affect the scoreline
    GOAL_TYPES = {EventType.GOAL, EventType.PENALTY_SCORED}
    OWN_GOAL_TYPES = {EventType.OWN_GOAL}

    match = models.ForeignKey(
        "competitions.Match",
        on_delete=models.CASCADE,
        related_name="events",
        verbose_name="Match",
    )
    tenant = models.ForeignKey(
        "core.Tenant",
        on_delete=models.CASCADE,
        related_name="match_events",
        verbose_name="Organization",
    )
    club = models.ForeignKey(
        "clubs.Club",
        on_delete=models.CASCADE,
        related_name="match_events",
        verbose_name="Club",
        help_text="Club the event is attributed to (attacker's club for goals, fouling club for cards).",
    )
    # Player may be null for manually entered results
    player = models.ForeignKey(
        "players.Player",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="match_events",
        verbose_name="Player",
    )
    # For substitutions: the player coming on/off pair
    player_off = models.ForeignKey(
        "players.Player",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="substituted_out_events",
        verbose_name="Player (Off)",
        help_text="Only used for SUBSTITUTION_IN — the player being replaced.",
    )

    event_type = models.CharField(
        max_length=30,
        choices=EventType.choices,
        verbose_name="Event Type",
    )
    minute = models.PositiveSmallIntegerField(
        verbose_name="Minute",
        help_text="Match minute when the event occurred (1-120, or 0 for pre-match).",
    )
    extra_time = models.BooleanField(
        default=False,
        verbose_name="Extra Time",
        help_text="True if the minute is in extra time / stoppage time.",
    )
    notes = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Notes",
    )

    class Meta:
        ordering = ["match", "minute"]
        verbose_name = "Match Event"
        verbose_name_plural = "Match Events"
        indexes = [
            models.Index(fields=["match", "minute"]),
            models.Index(fields=["player"]),
        ]

    def __str__(self) -> str:
        minute_str = f"{self.minute}+'" if self.extra_time else f"{self.minute}'"
        player_str = self.player.full_name if self.player else "Unknown"
        return f"[{self.match}] {minute_str} {self.get_event_type_display()} — {player_str}"

    @property
    def is_goal(self) -> bool:
        return self.event_type in self.GOAL_TYPES

    @property
    def is_own_goal(self) -> bool:
        return self.event_type in self.OWN_GOAL_TYPES
