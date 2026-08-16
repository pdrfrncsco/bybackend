from django.db import models

from common.models import BaseModel


class PlayerOnboardingStatus(BaseModel):
    """Tracks player onboarding progress through multiple steps.

    Onboarding is a multi-step process: account → identity → personal → football → contact → guardian → documents → club → review.
    Each step has a completion flag and optional data payload.
    """

    class Steps(models.TextChoices):
        ACCOUNT = "account", "Account Setup"
        IDENTITY = "identity", "Identity & Documents"
        PERSONAL = "personal", "Personal Information"
        FOOTBALL = "football", "Football Profile"
        CONTACT = "contact", "Contact Information"
        GUARDIAN = "guardian", "Guardian (if Minor)"
        DOCUMENTS = "documents", "Supporting Documents"
        CLUB = "club", "Club Registration"
        REVIEW = "review", "Final Review"

    STEP_ORDER = [
        Steps.ACCOUNT,
        Steps.IDENTITY,
        Steps.PERSONAL,
        Steps.FOOTBALL,
        Steps.CONTACT,
        Steps.GUARDIAN,
        Steps.DOCUMENTS,
        Steps.CLUB,
        Steps.REVIEW,
    ]

    player = models.OneToOneField(
        "players.Player",
        on_delete=models.CASCADE,
        related_name="onboarding_status",
        verbose_name="Player",
    )

    # Track completion per step
    account_complete = models.BooleanField(default=False)
    identity_complete = models.BooleanField(default=False)
    personal_complete = models.BooleanField(default=False)
    football_complete = models.BooleanField(default=False)
    contact_complete = models.BooleanField(default=False)
    guardian_complete = models.BooleanField(default=False)
    documents_complete = models.BooleanField(default=False)
    club_complete = models.BooleanField(default=False)
    review_complete = models.BooleanField(default=False)

    # Track progression
    current_step = models.CharField(
        max_length=50,
        choices=Steps.choices,
        default=Steps.ACCOUNT,
        verbose_name="Current Step",
    )
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Completed At")

    class Meta:
        verbose_name = "Player Onboarding Status"
        verbose_name_plural = "Player Onboarding Statuses"

    def __str__(self) -> str:
        try:
            return f"Onboarding: {self.player.full_name} — {self.current_step}"
        except Exception:
            return f"Onboarding: {self.player_id}"

    @property
    def is_complete(self) -> bool:
        """Return True if all steps are complete."""
        return all([
            self.account_complete,
            self.personal_complete,
            self.football_complete,
            self.contact_complete,
            # guardian_complete may not apply to all players (adults)
            self.documents_complete,
            self.club_complete,
            self.review_complete,
        ])

    @property
    def progress_percentage(self) -> int:
        """Return percentage of onboarding complete."""
        total_steps = len(self.STEP_ORDER) - 1  # identity is optional
        if self.player.is_minor:
            # All steps required for minors
            completed = sum([
                self.account_complete,
                self.personal_complete,
                self.football_complete,
                self.contact_complete,
                self.guardian_complete,
                self.documents_complete,
                self.club_complete,
                self.review_complete,
            ])
        else:
            # Adults skip guardian step
            total_steps -= 1
            completed = sum([
                self.account_complete,
                self.personal_complete,
                self.football_complete,
                self.contact_complete,
                self.documents_complete,
                self.club_complete,
                self.review_complete,
            ])
            total_steps -= 1
        
        return int((completed / total_steps * 100)) if total_steps > 0 else 0

    def get_next_step(self) -> str | None:
        """Return the next incomplete step, or None if onboarding is complete."""
        for step in self.STEP_ORDER:
            if step == self.Steps.IDENTITY:
                continue
            # Skip guardian for adults
            if step == self.Steps.GUARDIAN and not self.player.is_minor:
                continue
            
            step_complete = getattr(self, f"{step}_complete")
            if not step_complete:
                return step
        return None
