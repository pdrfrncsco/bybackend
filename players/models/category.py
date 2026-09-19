"""
BOLAYETU — PlayerCategory Model

Represents a football age category (escalão) defined by an Organization (Federation)
or customized by a Club.

Scope:
    - federation: official categories (e.g. Petiz, Traquina, Benjamim, Infantil, Iniciado, Juvenil, Júnior, Sénior, Veterano)
    - club: custom categories defined by a specific club (e.g. Sub-17, Sub-15, Equipa B)
"""

from django.db import models
from django.utils.text import slugify

from common.models import BaseModel


class PlayerCategory(BaseModel):
    """
    Age and gender category for football players and squad management.
    """

    class Scope(models.TextChoices):
        FEDERATION = "federation", "Federação"
        CLUB = "club", "Clube"

    class Gender(models.TextChoices):
        MALE = "male", "Masculino"
        FEMALE = "female", "Feminino"
        MIXED = "mixed", "Misto"

    tenant = models.ForeignKey(
        "core.Tenant",
        on_delete=models.CASCADE,
        related_name="player_categories",
        verbose_name="Organização / Federação",
    )
    club = models.ForeignKey(
        "clubs.Club",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="custom_categories",
        verbose_name="Clube",
        help_text="Preenchido quando a categoria é personalizada pelo clube.",
    )
    scope = models.CharField(
        max_length=20,
        choices=Scope.choices,
        default=Scope.FEDERATION,
        verbose_name="Âmbito",
    )
    name = models.CharField(max_length=100, verbose_name="Nome da Categoria")
    slug = models.SlugField(max_length=100, verbose_name="Slug")
    min_age = models.PositiveIntegerField(null=True, blank=True, verbose_name="Idade Mínima")
    max_age = models.PositiveIntegerField(null=True, blank=True, verbose_name="Idade Máxima")
    gender = models.CharField(
        max_length=10,
        choices=Gender.choices,
        default=Gender.MIXED,
        verbose_name="Género Elegível",
    )
    is_custom = models.BooleanField(default=False, verbose_name="É Personalizada?")
    is_active = models.BooleanField(default=True, verbose_name="Ativa")
    display_order = models.PositiveIntegerField(default=0, verbose_name="Ordem de Exibição")

    class Meta:
        ordering = ["display_order", "min_age", "name"]
        verbose_name = "Categoria de Jogador"
        verbose_name_plural = "Categorias de Jogadores"
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "club", "slug"],
                name="unique_category_slug_per_tenant_club",
            ),
        ]

    def __str__(self) -> str:
        age_str = ""
        if self.min_age and self.max_age:
            age_str = f" ({self.min_age}-{self.max_age} anos)"
        elif self.min_age:
            age_str = f" (+{self.min_age} anos)"
        elif self.max_age:
            age_str = f" (até {self.max_age} anos)"
        return f"{self.name}{age_str}"

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            base = slugify(self.name)
            slug = base
            counter = 1
            while PlayerCategory.objects.filter(tenant=self.tenant, club=self.club, slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        if self.club_id:
            self.scope = self.Scope.CLUB
            self.is_custom = True
        else:
            self.scope = self.Scope.FEDERATION
            self.is_custom = False
        super().save(*args, **kwargs)
