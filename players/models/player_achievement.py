"""
BOLAYETU — PlayerAchievement Model

Represents achievements, trophies, and awards won by a player.

Architecture:
    - PlayerAchievement is a GLOBAL entity — linked to a Player (not tenant-scoped).
    - Tracks titles, awards, and honors across the player's entire career.
    - Can be associated with a competition, club, or standalone achievements.
"""

from django.db import models

from common.models import BaseModel


class PlayerAchievement(BaseModel):
    """
    Represents an achievement, trophy, or award won by a player.
    
    Achievements can be:
        - Competition titles (league winners, cup winners)
        - Individual awards (best player, top scorer, MVP)
        - Career milestones (100 goals, 500 appearances)
        - International honors (national team caps, tournaments)
    """

    class AchievementType(models.TextChoices):
        # Team achievements
        LEAGUE_TITLE = "league_title", "Título de Liga"
        CUP_TITLE = "cup_title", "Título de Taça"
        SUPER_CUP = "super_cup", "Super Taça"
        TOURNAMENT = "tournament", "Torneio"
        INTERNATIONAL_CLUB = "international_club", "Competição Internacional de Clubes"
        
        # Individual awards
        TOP_SCORER = "top_scorer", "Melhor Marcador"
        BEST_PLAYER = "best_player", "Melhor Jogador"
        MVP = "mvp", "Jogador Mais Valioso"
        BEST_GOALKEEPER = "best_goalkeeper", "Melhor Guarda-Redes"
        BEST_YOUNG_PLAYER = "best_young_player", "Melhor Jovem"
        GOLDEN_BOOT = "golden_boot", "Chuteira de Ouro"
        GOLDEN_BALL = "golden_ball", "Bola de Ouro"
        
        # Career milestones
        MILESTONE_100_GOALS = "milestone_100_goals", "100 Golos"
        MILESTONE_500_APPEARANCES = "milestone_500_appearances", "500 Jogos"
        MILESTONE_100_CAPS = "milestone_100_caps", "100 Internacionalizações"
        
        # International honors
        NATIONAL_TEAM_CAP = "national_team_cap", "Internacionalização"
        WORLD_CUP = "world_cup", "Copa do Mundo"
        CONTINENTAL_CUP = "continental_cup", "Copa Continental"
        OLYMPICS = "olympics", "Jogos Olímpicos"
        
        # Other
        OTHER = "other", "Outro"

    class AchievementLevel(models.TextChoices):
        CLUB = "club", "Nível de Clube"
        NATIONAL = "national", "Nível Nacional"
        CONTINENTAL = "continental", "Nível Continental"
        INTERNATIONAL = "international", "Nível Internacional"
        WORLD = "world", "Nível Mundial"

    # Player reference (global entity)
    player = models.ForeignKey(
        "players.Player",
        on_delete=models.CASCADE,
        related_name="achievements",
        verbose_name="Player",
    )

    # Achievement details
    title = models.CharField(
        max_length=255,
        verbose_name="Title",
        help_text="Achievement title (e.g., 'Campeão da Girabola 2025')",
    )
    achievement_type = models.CharField(
        max_length=30,
        choices=AchievementType.choices,
        default=AchievementType.OTHER,
        verbose_name="Achievement Type",
    )
    level = models.CharField(
        max_length=20,
        choices=AchievementLevel.choices,
        default=AchievementLevel.CLUB,
        verbose_name="Achievement Level",
    )
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name="Description",
        help_text="Additional details about the achievement",
    )

    # Date and season
    date_achieved = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date Achieved",
    )
    season = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="Season",
        help_text="Season when achievement was won (e.g., '2024/2025')",
    )

    # Context associations (optional)
    competition = models.ForeignKey(
        "competitions.Competition",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="player_achievements",
        verbose_name="Competition",
        help_text="Competition this achievement is related to",
    )
    club = models.ForeignKey(
        "clubs.Club",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="player_achievements",
        verbose_name="Club",
        help_text="Club the player was at when achieving this",
    )

    # Media
    trophy_asset = models.ForeignKey(
        "media_assets.MediaAsset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="player_achievement_trophies",
        verbose_name="Trophy Asset",
        help_text="Uploaded trophy image via DAM",
    )
    certificate_asset = models.ForeignKey(
        "media_assets.MediaAsset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="player_achievement_certificates",
        verbose_name="Certificate Asset",
        help_text="Uploaded certificate via DAM",
    )
    trophy_image = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name="Trophy Image URL",
    )
    certificate_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name="Certificate URL",
    )

    # Additional stats for context
    stats_snapshot = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Stats Snapshot",
        help_text="Player stats at the time of achievement (goals, assists, matches)",
    )

    # Verification
    is_verified = models.BooleanField(
        default=False,
        verbose_name="Is Verified",
        help_text="Verified achievements have been confirmed by officials",
    )

    class Meta:
        ordering = ["-date_achieved", "-created_at"]
        verbose_name = "Player Achievement"
        verbose_name_plural = "Player Achievements"
        indexes = [
            models.Index(fields=["player", "achievement_type"]),
            models.Index(fields=["player", "date_achieved"]),
            models.Index(fields=["player", "season"]),
            models.Index(fields=["player", "is_verified"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} — {self.player.full_name}"

    @property
    def year(self) -> int | None:
        """Return the year the achievement was won."""
        if self.date_achieved:
            return self.date_achieved.year
        if self.season:
            # Extract year from season like "2024/2025"
            try:
                return int(self.season.split("/")[0])
            except (ValueError, IndexError):
                pass
        return None
