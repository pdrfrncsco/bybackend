"""
BOLAYETU — CompetitionRanking Model

Represents cross-competition rankings and aggregations.
Rankings can be:
    - Top scorers across all competitions in a season
    - Fair play rankings (clubs/players with fewest cards)
    - Historical club rankings (all-time points, titles, etc.)
    - Player global rankings (total goals, assists, appearances)

Architecture:
    - CompetitionRanking is tenant-scoped
    - Supports different ranking types and aggregation levels
    - Updated periodically or on-demand via RankingService
"""

from django.db import models
from common.models import BaseModel


class CompetitionRanking(BaseModel):
    """
    Represents a ranking entry for a player or club.
    
    Rankings are calculated and stored for quick retrieval.
    They can be cross-competition (season-wide) or competition-specific.
    """

    class RankingType(models.TextChoices):
        TOP_SCORER = "top_scorer", "Melhor Marcador"
        TOP_ASSISTS = "top_assists", "Mais Assistências"
        FAIR_PLAY_PLAYER = "fair_play_player", "Fair Play (Jogador)"
        FAIR_PLAY_CLUB = "fair_play_club", "Fair Play (Clube)"
        HISTORICAL_POINTS = "historical_points", "Pontos Históricos"
        HISTORICAL_TITLES = "historical_titles", "Títulos Históricos"
        MOST_APPEARANCES = "most_appearances", "Mais Partidas"
        MOST_CLEAN_SHEETS = "most_clean_sheets", "Mais Clean Sheets"
        PLAYER_OF_THE_YEAR = "player_of_the_year", "Jogador do Ano"
        YOUNG_PLAYER = "young_player", "Jogador Jovem"

    class AggregationLevel(models.TextChoices):
        COMPETITION = "competition", "Por Competição"
        SEASON = "season", "Por Temporada"
        ALL_TIME = "all_time", "Histórico"
        MONTHLY = "monthly", "Mensal"

    # ─── Core Relations ─────────────────────────────────────────────────────
    tenant = models.ForeignKey(
        "core.Tenant",
        on_delete=models.CASCADE,
        related_name="rankings",
        verbose_name="Organization",
    )
    
    # Optional: specific competition (null for cross-competition rankings)
    competition = models.ForeignKey(
        "competitions.Competition",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="rankings",
        verbose_name="Competition",
        help_text="Specific competition (null for cross-competition rankings).",
    )
    
    # Subject: player or club (one must be set)
    player = models.ForeignKey(
        "players.Player",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="rankings",
        verbose_name="Player",
    )
    club = models.ForeignKey(
        "clubs.Club",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="rankings",
        verbose_name="Club",
    )

    # ─── Ranking Details ────────────────────────────────────────────────────
    ranking_type = models.CharField(
        max_length=30,
        choices=RankingType.choices,
        verbose_name="Ranking Type",
    )
    aggregation_level = models.CharField(
        max_length=20,
        choices=AggregationLevel.choices,
        default=AggregationLevel.SEASON,
        verbose_name="Aggregation Level",
    )
    
    # ─── Season/Period ───────────────────────────────────────────────────────
    season = models.CharField(
        max_length=20,
        blank=True,
        default="",
        verbose_name="Season",
        help_text="e.g., '2024/2025', '2025'.",
    )
    month = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="Month",
        help_text="For monthly rankings (1-12).",
    )
    year = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Year",
        help_text="Year for annual or monthly rankings.",
    )

    # ─── Position & Stats ────────────────────────────────────────────────────
    position = models.PositiveIntegerField(
        verbose_name="Position",
        help_text="Current position in the ranking.",
    )
    previous_position = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Previous Position",
        help_text="Position in the last update.",
    )
    
    # Value (points, goals, etc.)
    value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Value",
        help_text="The ranking value (goals, points, fair play score, etc.).",
    )
    
    # Detailed stats (JSON for flexibility)
    stats = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Statistics",
        help_text="Detailed stats for this ranking entry.",
    )

    # ─── Status ──────────────────────────────────────────────────────────────
    is_official = models.BooleanField(
        default=False,
        verbose_name="Is Official",
        help_text="Whether this is an officially verified ranking.",
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name="Last Updated",
    )

    class Meta:
        ordering = ["ranking_type", "season", "position"]
        verbose_name = "Competition Ranking"
        verbose_name_plural = "Competition Rankings"
        indexes = [
            models.Index(fields=["ranking_type", "season", "position"]),
            models.Index(fields=["player", "ranking_type"]),
            models.Index(fields=["club", "ranking_type"]),
            models.Index(fields=["tenant", "ranking_type", "season"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "ranking_type", "aggregation_level", "season", "player"],
                name="unique_player_ranking_per_season",
                condition=models.Q(player__isnull=False),
            ),
            models.UniqueConstraint(
                fields=["tenant", "ranking_type", "aggregation_level", "season", "club"],
                name="unique_club_ranking_per_season",
                condition=models.Q(club__isnull=False),
            ),
        ]

    def __str__(self) -> str:
        subject = self.player.full_name if self.player else self.club.name if self.club else "Unknown"
        season_str = f" ({self.season})" if self.season else ""
        return f"#{self.position} {subject} - {self.get_ranking_type_display()}{season_str}"

    @property
    def position_change(self) -> int | None:
        """Calculate position change from previous update."""
        if self.previous_position is None:
            return None
        return self.previous_position - self.position  # Positive = moved up, Negative = moved down

    @property
    def moved_up(self) -> bool | None:
        """Check if position improved."""
        change = self.position_change
        return change > 0 if change is not None else None

    @property
    def moved_down(self) -> bool | None:
        """Check if position worsened."""
        change = self.position_change
        return change < 0 if change is not None else None

    def update_position(self, new_position: int) -> None:
        """Update position and track previous position."""
        self.previous_position = self.position
        self.position = new_position
        self.save(update_fields=["position", "previous_position", "updated_at"])
