"""
BOLAYETU — Fans & Community Engagement Models
"""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import UUIDModel, TimeStampedModel


class FanProfile(UUIDModel, TimeStampedModel):
    """
    Business profile for platform Fans/Supporters.
    Attached 1-to-1 with global User account.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="fan_profile",
        verbose_name=_("User"),
    )
    favorite_club = models.ForeignKey(
        "clubs.Club",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fan_supporters",
        verbose_name=_("Favorite Club"),
    )
    bio = models.TextField(
        blank=True,
        verbose_name=_("Biography"),
    )
    location = models.CharField(
        max_length=150,
        blank=True,
        verbose_name=_("City / Province"),
    )
    notification_match_start = models.BooleanField(
        default=True,
        verbose_name=_("Notify Match Start"),
    )
    notification_goals = models.BooleanField(
        default=True,
        verbose_name=_("Notify Goals & Results"),
    )
    notification_transfers = models.BooleanField(
        default=True,
        verbose_name=_("Notify Transfers"),
    )
    points = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Prediction Points"),
    )
    correct_predictions_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Correct Predictions"),
    )
    total_predictions_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Total Predictions"),
    )
    badges = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("Earned Badges"),
    )

    class Meta:
        verbose_name = _("Fan Profile")
        verbose_name_plural = _("Fan Profiles")

    def __str__(self) -> str:
        return f"FanProfile({self.user.email} - {self.points} pts)"


class FollowTargetType(models.TextChoices):
    CLUB = "club", _("Club")
    PLAYER = "player", _("Player")
    COMPETITION = "competition", _("Competition")


class FanFollow(UUIDModel, TimeStampedModel):
    """
    Stores followed entities (Clubs, Players, Competitions) for personalized feeds and alerts.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="fan_follows",
        verbose_name=_("User"),
    )
    target_type = models.CharField(
        max_length=20,
        choices=FollowTargetType.choices,
        verbose_name=_("Target Type"),
    )
    club = models.ForeignKey(
        "clubs.Club",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="fan_followers",
        verbose_name=_("Followed Club"),
    )
    player = models.ForeignKey(
        "players.Player",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="fan_followers",
        verbose_name=_("Followed Player"),
    )
    competition = models.ForeignKey(
        "competitions.Competition",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="fan_followers",
        verbose_name=_("Followed Competition"),
    )

    class Meta:
        verbose_name = _("Fan Follow")
        verbose_name_plural = _("Fan Follows")
        constraints = [
            models.UniqueConstraint(
                fields=["user", "target_type", "club"],
                condition=models.Q(club__isnull=False),
                name="unique_user_club_follow",
            ),
            models.UniqueConstraint(
                fields=["user", "target_type", "player"],
                condition=models.Q(player__isnull=False),
                name="unique_user_player_follow",
            ),
            models.UniqueConstraint(
                fields=["user", "target_type", "competition"],
                condition=models.Q(competition__isnull=False),
                name="unique_user_competition_follow",
            ),
        ]

    def __str__(self) -> str:
        target = self.club or self.player or self.competition
        return f"{self.user.email} -> {self.target_type}:{target}"


class PredictionStatus(models.TextChoices):
    PENDING = "pending", _("Pending")
    EVALUATED = "evaluated", _("Evaluated")
    CANCELLED = "cancelled", _("Cancelled")


class MatchPrediction(UUIDModel, TimeStampedModel):
    """
    Score prediction submitted by a fan for an upcoming match in the platform.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="match_predictions",
        verbose_name=_("User"),
    )
    match = models.ForeignKey(
        "competitions.Match",
        on_delete=models.CASCADE,
        related_name="fan_predictions",
        verbose_name=_("Match"),
    )
    predicted_home_score = models.PositiveSmallIntegerField(
        verbose_name=_("Predicted Home Score"),
    )
    predicted_away_score = models.PositiveSmallIntegerField(
        verbose_name=_("Predicted Away Score"),
    )
    status = models.CharField(
        max_length=20,
        choices=PredictionStatus.choices,
        default=PredictionStatus.PENDING,
        verbose_name=_("Status"),
    )
    points_awarded = models.PositiveSmallIntegerField(
        default=0,
        verbose_name=_("Points Awarded"),
    )
    evaluated_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Evaluated At"),
    )

    class Meta:
        verbose_name = _("Match Prediction")
        verbose_name_plural = _("Match Predictions")
        constraints = [
            models.UniqueConstraint(
                fields=["user", "match"],
                name="unique_user_match_prediction",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user.email} predicted {self.predicted_home_score}-{self.predicted_away_score} for Match({self.match_id})"


class FanMVPVote(UUIDModel, TimeStampedModel):
    """
    Fan vote for Match MVP / Man of the Match.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="fan_mvp_votes",
        verbose_name=_("User"),
    )
    match = models.ForeignKey(
        "competitions.Match",
        on_delete=models.CASCADE,
        related_name="fan_mvp_votes",
        verbose_name=_("Match"),
    )
    player = models.ForeignKey(
        "players.Player",
        on_delete=models.CASCADE,
        related_name="fan_mvp_votes",
        verbose_name=_("Voted Player"),
    )

    class Meta:
        verbose_name = _("Fan MVP Vote")
        verbose_name_plural = _("Fan MVP Votes")
        constraints = [
            models.UniqueConstraint(
                fields=["user", "match"],
                name="unique_user_match_mvp_vote",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user.email} voted {self.player_id} MVP for Match({self.match_id})"
