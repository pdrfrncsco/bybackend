"""
BOLAYETU — Player Registration Request Model

Formal request for a global player to link with a club.
Approved requests create a PlayerRegistration record.
"""

from django.conf import settings
from django.db import models

from common.models import BaseModel


class PlayerRegistrationRequest(BaseModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        INVITED = "invited", "Convidado"
        APPROVED = "approved", "Aprovado"
        REJECTED = "rejected", "Rejeitado"

    player = models.ForeignKey(
        "players.Player",
        on_delete=models.CASCADE,
        related_name="registration_requests",
        verbose_name="Player",
    )
    club = models.ForeignKey(
        "clubs.Club",
        on_delete=models.CASCADE,
        related_name="player_registration_requests",
        verbose_name="Club",
    )
    tenant = models.ForeignKey(
        "core.Tenant",
        on_delete=models.CASCADE,
        related_name="player_registration_requests",
        verbose_name="Tenant",
    )
    competition = models.ForeignKey(
        "competitions.Competition",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="player_registration_requests",
        verbose_name="Competition",
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="player_registration_requests_submitted",
        verbose_name="Submitted By",
    )
    joined_date = models.DateField(verbose_name="Requested Join Date")
    shirt_number = models.IntegerField(null=True, blank=True, verbose_name="Shirt Number")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Status",
    )
    review_notes = models.TextField(blank=True, default="", verbose_name="Review Notes")
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="player_registration_requests_reviewed",
        verbose_name="Reviewed By",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name="Reviewed At")
    registration = models.OneToOneField(
        "players.PlayerRegistration",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="registration_request",
        verbose_name="Created Registration",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Player Registration Request"
        verbose_name_plural = "Player Registration Requests"
        indexes = [
            models.Index(fields=["club", "status"]),
            models.Index(fields=["player", "status"]),
            models.Index(fields=["tenant", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.player.full_name} → {self.club.name} ({self.status})"
