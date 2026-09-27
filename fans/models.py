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


# ─────────────────────────────────────────────────────────────────────
# CONTENT PUBLISHING MODULE ("PUBLICAR NO FEED")
# ─────────────────────────────────────────────────────────────────────

class PostAuthorType(models.TextChoices):
    ORGANIZATION = "organization", _("Organização / Federação")
    CLUB = "club", _("Clube Oficial")
    PLAYER = "player", _("Jogador")


class PostCategory(models.TextChoices):
    GENERAL = "general", _("Geral")
    MATCHDAY = "matchday", _("Dia de Jogo / Convocatória")
    ANNOUNCEMENT = "announcement", _("Comunicado Oficial")
    TRAINING = "training", _("Treino & Bastidores")
    HIGHLIGHT = "highlight", _("Vídeo & Lance")


class FeedPost(UUIDModel, TimeStampedModel):
    """
    Rich social & editorial post published by an Organization, Club, or Player to the Fan Feed.
    """

    author_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="authored_feed_posts",
        verbose_name=_("Author User"),
    )
    author_type = models.CharField(
        max_length=20,
        choices=PostAuthorType.choices,
        verbose_name=_("Author Type"),
    )
    organization = models.ForeignKey(
        "core.Tenant",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="feed_posts",
        verbose_name=_("Organization"),
    )
    club = models.ForeignKey(
        "clubs.Club",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="feed_posts",
        verbose_name=_("Club"),
    )
    player = models.ForeignKey(
        "players.Player",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="feed_posts",
        verbose_name=_("Player"),
    )
    category = models.CharField(
        max_length=20,
        choices=PostCategory.choices,
        default=PostCategory.GENERAL,
        verbose_name=_("Category"),
    )
    title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Title / Headline"),
    )
    content = models.TextField(
        verbose_name=_("Content / Text"),
    )
    media_url = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name=_("Media URL (Photo/Video)"),
    )
    is_official = models.BooleanField(
        default=True,
        verbose_name=_("Official Post"),
    )
    is_pinned = models.BooleanField(
        default=False,
        verbose_name=_("Pinned Post"),
    )
    likes_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Likes Count"),
    )
    comments_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Comments Count"),
    )

    class Meta:
        verbose_name = _("Feed Post")
        verbose_name_plural = _("Feed Posts")
        ordering = ["-is_pinned", "-created_at"]

    def __str__(self) -> str:
        entity = self.club or self.player or self.organization or self.author_user
        return f"FeedPost({self.author_type}:{entity} - {self.category})"


class FeedPostLike(UUIDModel, TimeStampedModel):
    """
    User like on a specific FeedPost.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="feed_post_likes",
        verbose_name=_("User"),
    )
    post = models.ForeignKey(
        FeedPost,
        on_delete=models.CASCADE,
        related_name="likes",
        verbose_name=_("Post"),
    )

    class Meta:
        verbose_name = _("Feed Post Like")
        verbose_name_plural = _("Feed Post Likes")
        constraints = [
            models.UniqueConstraint(
                fields=["user", "post"],
                name="unique_user_feed_post_like",
            ),
        ]


class FeedPostComment(UUIDModel, TimeStampedModel):
    """
    Comment on a FeedPost with moderation status.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="feed_post_comments",
        verbose_name=_("User"),
    )
    post = models.ForeignKey(
        FeedPost,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name=_("Post"),
    )
    content = models.TextField(
        verbose_name=_("Comment Content"),
    )
    is_moderated = models.BooleanField(
        default=False,
        verbose_name=_("Is Moderated"),
    )

    class Meta:
        verbose_name = _("Feed Post Comment")
        verbose_name_plural = _("Feed Post Comments")
        ordering = ["created_at"]
