"""
BOLAYETU — PlayerVideo Model

Represents video content associated with a player (highlights, interviews, skills showcase).

Architecture:
    - PlayerVideo is a GLOBAL entity — linked to a Player (not tenant-scoped).
    - Uses MediaAsset for actual file storage via MediaUsage.
    - Supports multiple video categories: highlights, interviews, skills, etc.
"""

from django.db import models
from common.models import BaseModel


class PlayerVideo(BaseModel):
    """
    Represents a video associated with a player profile.
    
    Videos can be:
        - Highlights (best plays, goals, assists)
        - Skills showcase (training drills, techniques)
        - Interviews and media appearances
        - Match footage clips
    
    The actual video file is stored via MediaAsset (DAM integration).
    """

    class VideoType(models.TextChoices):
        HIGHLIGHTS = "highlights", "Melhores Momentos"
        SKILLS = "skills", "Demonstração de Skills"
        INTERVIEW = "interview", "Entrevista"
        MATCH_CLIP = "match_clip", "Clip de Jogo"
        TRAINING = "training", "Treino"
        OTHER = "other", "Outro"

    class VideoStatus(models.TextChoices):
        DRAFT = "draft", "Rascunho"
        PUBLISHED = "published", "Publicado"
        ARCHIVED = "archived", "Arquivado"

    # Player reference (global entity)
    player = models.ForeignKey(
        "players.Player",
        on_delete=models.CASCADE,
        related_name="videos",
        verbose_name="Player",
    )

    # Video metadata
    title = models.CharField(
        max_length=255,
        verbose_name="Title",
        help_text="Video title (e.g., 'Golo frente ao Petro - Girabola 2025')",
    )
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name="Description",
        help_text="Optional description or context for the video",
    )
    video_type = models.CharField(
        max_length=20,
        choices=VideoType.choices,
        default=VideoType.HIGHLIGHTS,
        verbose_name="Video Type",
    )

    # Video source — either uploaded via DAM or external URL
    video_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name="Video URL",
        help_text="External video URL (YouTube, Vimeo, etc.)",
    )
    thumbnail_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name="Thumbnail URL",
    )

    # DAM integration — link to MediaAsset for uploaded videos
    media_asset = models.ForeignKey(
        "media_assets.MediaAsset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="player_videos",
        verbose_name="Media Asset",
        help_text="Uploaded video file via DAM",
    )

    # Video metadata from processing
    duration_seconds = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Duration (seconds)",
    )

    # Status and visibility
    status = models.CharField(
        max_length=20,
        choices=VideoStatus.choices,
        default=VideoStatus.PUBLISHED,
        verbose_name="Status",
    )
    is_featured = models.BooleanField(
        default=False,
        verbose_name="Is Featured",
        help_text="Featured videos appear prominently on the player profile",
    )

    # Ordering for profile display
    order = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Order",
        help_text="Display order on player profile",
    )

    # Source context (optional)
    match = models.ForeignKey(
        "competitions.Match",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="player_videos",
        verbose_name="Related Match",
        help_text="Match this video is from (if applicable)",
    )

    class Meta:
        ordering = ["-is_featured", "order", "-created_at"]
        verbose_name = "Player Video"
        verbose_name_plural = "Player Videos"
        indexes = [
            models.Index(fields=["player", "status"]),
            models.Index(fields=["player", "video_type"]),
            models.Index(fields=["player", "is_featured"]),
        ]

    def __str__(self) -> str:
        return f"{self.player.full_name} — {self.title}"

    @property
    def url(self) -> str | None:
        """Return the best available video URL."""
        if self.video_url:
            return self.video_url
        if self.media_asset:
            return self.media_asset.public_url
        return None

    @property
    def thumbnail(self) -> str | None:
        """Return the best available thumbnail URL."""
        if self.thumbnail_url:
            return self.thumbnail_url
        if self.media_asset and self.media_asset.thumbnail_url:
            return self.media_asset.thumbnail_url
        return None
