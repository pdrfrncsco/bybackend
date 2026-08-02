from django.db import models
import uuid
from common.models import BaseModel


class TacticalPositions(BaseModel):
    """Store tactical player positions for a match + club.

    Fields:
      - tenant: organization tenant
      - match: FK to Match
      - club: FK to Club
      - positions: JSON blob with list of { player_id, x, y, number?, name? }
      - version: optimistic concurrency UUID (changes on each write)
      - updated_at from BaseModel used for timestamp
    """

    tenant = models.ForeignKey(
        "core.Tenant",
        on_delete=models.CASCADE,
        related_name="tactical_positions",
        verbose_name="Organization",
    )

    match = models.ForeignKey(
        "competitions.Match",
        on_delete=models.CASCADE,
        related_name="tactical_positions",
        verbose_name="Match",
    )

    club = models.ForeignKey(
        "clubs.Club",
        on_delete=models.CASCADE,
        related_name="tactical_positions",
        verbose_name="Club",
    )

    positions = models.JSONField(default=list, blank=True)

    version = models.UUIDField(default=uuid.uuid4, editable=False)

    class Meta:
        verbose_name = "Tactical Positions"
        verbose_name_plural = "Tactical Positions"
        constraints = [
            models.UniqueConstraint(fields=["match", "club"], name="unique_tactical_per_match_club"),
        ]

    def touch_version(self):
        self.version = uuid.uuid4()
        self.save(update_fields=["version", "updated_at"])

        def can_user_modify(self, user):
            """Check if a user can modify tactical positions for this club."""
            # Allow superusers
            if user.is_superuser:
                return True
            try:
                from clubs.models import ClubMember
                return ClubMember.objects.filter(club=self.club, user=user, is_active=True, role__in=["manager", "coach", "assistant_coach"]).exists()
            except Exception:
                return False

    def __str__(self) -> str:
        return f"TacticalPositions(match={self.match}, club={self.club}, updated_at={self.updated_at})"
