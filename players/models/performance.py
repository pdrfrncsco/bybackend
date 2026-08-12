"""
BOLAYETU — Player Performance Metric Model

Represents GPS and biometric performance data for players.
Used for performance analysis, injury prevention, and player development.
"""

from django.db import models
from common.models import BaseModel


class PlayerPerformanceMetric(BaseModel):
    """GPS/Biometric performance metric for a player."""

    class MetricType(models.TextChoices):
        # Speed Metrics
        MAX_SPEED = "max_speed", "Velocidade Máxima (km/h)"
        AVG_SPEED = "avg_speed", "Velocidade Média (km/h)"
        SPRINT_SPEED = "sprint_speed", "Velocidade de Sprint (km/h)"
        
        # Distance Metrics
        TOTAL_DISTANCE = "total_distance", "Distância Total (m)"
        SPRINT_DISTANCE = "sprint_distance", "Distância em Sprint (m)"
        HIGH_SPEED_DISTANCE = "high_speed_distance", "Distância Alta Velocidade (m)"
        
        # Physical Metrics
        SPRINTS_COUNT = "sprints_count", "Número de Sprints"
        ACCELERATIONS = "accelerations", "Acelerações"
        DECELERATIONS = "decelerations", "Desacelerações"
        JUMPS = "jumps", "Saltos"
        
        # Biometric Metrics
        MAX_HEART_RATE = "max_heart_rate", "Frequência Cardíaca Máxima (bpm)"
        AVG_HEART_RATE = "avg_heart_rate", "Frequência Cardíaca Média (bpm)"
        HEART_RATE_ZONES = "heart_rate_zones", "Tempo por Zonas Cardíacas"
        
        # Workload Metrics
        PLAYER_LOAD = "player_load", "Carga de Trabalho"
        TRAINING_LOAD = "training_load", "Carga de Treino"
        MATCH_LOAD = "match_load", "Carga de Jogo"
        
        # Recovery Metrics
        RECOVERY_TIME = "recovery_time", "Tempo de Recuperação (h)"
        FATIGUE_INDEX = "fatigue_index", "Índice de Fadiga"
        
        # Other
        OTHER = "other", "Outro"

    class MetricSource(models.TextChoices):
        GPS = "gps", "Dispositivo GPS"
        WEARABLE = "wearable", "Dispositivo Vestível"
        MANUAL = "manual", "Registo Manual"
        VIDEO_ANALYSIS = "video_analysis", "Análise de Vídeo"
        CLUB_SYSTEM = "club_system", "Sistema do Clube"
        OTHER = "other", "Outro"

    # Relations
    player = models.ForeignKey(
        "players.Player",
        on_delete=models.CASCADE,
        related_name="performance_metrics",
        verbose_name="Jogador",
    )
    match = models.ForeignKey(
        "competitions.Match",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="player_performance_metrics",
        verbose_name="Jogo",
        help_text="Se aplicável, o jogo associado a esta métrica",
    )

    # Metric Details
    recorded_at = models.DateTimeField(
        verbose_name="Data de Registo",
    )
    metric_type = models.CharField(
        max_length=30,
        choices=MetricType.choices,
        verbose_name="Tipo de Métrica",
    )
    value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Valor",
    )
    unit = models.CharField(
        max_length=20,
        verbose_name="Unidade",
        help_text="Ex: km/h, m, bpm, etc.",
    )

    # Source
    source = models.CharField(
        max_length=20,
        choices=MetricSource.choices,
        default=MetricSource.GPS,
        verbose_name="Fonte",
    )
    device_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="ID do Dispositivo",
        help_text="Identificador do dispositivo que capturou a métrica",
    )

    # Context
    training_session = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Sessão de Treino",
        help_text="Identificador da sessão de treino, se aplicável",
    )
    position_during_metric = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Posição Durante Métrica",
        help_text="Posição do jogador quando a métrica foi registada",
    )

    # Additional Data
    additional_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Dados Adicionais",
        help_text="Dados estruturados adicionais (ex: zonas cardíacas, distribuição de velocidade)",
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Notas",
    )

    class Meta:
        verbose_name = "Métrica de Performance"
        verbose_name_plural = "Métricas de Performance"
        ordering = ["-recorded_at"]
        indexes = [
            models.Index(fields=["player", "recorded_at"]),
            models.Index(fields=["metric_type"]),
            models.Index(fields=["match"]),
        ]

    def __str__(self) -> str:
        return f"{self.player.full_name} - {self.get_metric_type_display()}: {self.value} {self.unit}"
