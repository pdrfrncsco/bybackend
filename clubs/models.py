from django.db import models
from django.core.validators import RegexValidator
from core.models import BaseModel, Tenant
# from estadios.models import Stadium # Commented out as it seems to cause issues if not present or circular

class Club(BaseModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='clubs')
    name = models.CharField(max_length=255)
    acronym = models.CharField(
        max_length=3,
        blank=True,
        validators=[
            RegexValidator(
                regex=r"^[A-Z]{3}$",
                message="A sigla deve ter exatamente 3 letras maiúsculas.",
                code="invalid_acronym",
            )
        ],
    )
    short_name = models.CharField(max_length=12, blank=True)
    founded_year = models.IntegerField(null=True, blank=True)
    logo = models.ImageField(upload_to='clubs/', null=True, blank=True)
    location = models.CharField(max_length=255, blank=True)
    president = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    stadium_name = models.CharField(max_length=255, blank=True)
    stadium_capacity = models.IntegerField(null=True, blank=True) # Added capacity
    primary_color = models.CharField(max_length=7, blank=True)
    secondary_color = models.CharField(max_length=7, blank=True)
    active_players = models.IntegerField(default=0) # Added active_players count cache
    organizacao = models.ForeignKey(
        'accounts.OrganizacaoProfile',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='associated_clubs'
    )
    clube_profile = models.OneToOneField(
        'accounts.ClubeProfile',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='business_club'
    )

    def __str__(self):
        return self.name

class ClubHistory(BaseModel):
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='history')
    season = models.CharField(max_length=20)
    tournament_name = models.CharField(max_length=255)
    placement = models.CharField(max_length=50)
    is_trophy = models.BooleanField(default=False)

    class Meta:
        ordering = ['-season']

    def __str__(self):
        return f"{self.club.name} - {self.season}"

class Staff(BaseModel):
    tenant = models.ForeignKey(
        Tenant, 
        on_delete=models.CASCADE, 
        related_name='staff',
        help_text="A organização à qual esta staff pertence."
    )
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='staff_members', blank=True, null=True)
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100) # Ex: Treinador Principal, Fisioterapeuta
    date_of_birth = models.DateField(blank=True, null=True)
    nationality = models.CharField(max_length=50, blank=True, null=True)
    photo = models.ImageField(upload_to='staff_photos/', blank=True, null=True)
    
    # Contact info
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        verbose_name = "Membro da Equipa Técnica"
        verbose_name_plural = "Membros da Equipa Técnica"
        unique_together = ('tenant', 'name', 'club')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.role})"
