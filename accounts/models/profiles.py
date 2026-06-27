from django.db import models
from django.conf import settings
from core.models import BaseModel


class OrganizacaoProfile(BaseModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organizacao_profile"
    )
    nome = models.CharField(max_length=255)
    sigla = models.CharField(max_length=50, blank=True)
    descricao = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    telefone = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    pais = models.CharField(max_length=100, blank=True)
    provincia = models.CharField(max_length=100, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    logo = models.ImageField(upload_to="organizacoes/logos/", null=True, blank=True)
    banner = models.ImageField(upload_to="organizacoes/banners/", null=True, blank=True)
    status = models.CharField(max_length=20, default="active")

    class Meta:
        verbose_name = "Perfil de Organização"
        verbose_name_plural = "Perfis de Organizações"

    def __str__(self):
        return self.nome


class ClubeProfile(BaseModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="clube_profile"
    )
    nome = models.CharField(max_length=255)
    sigla = models.CharField(max_length=50, blank=True)
    fundacao = models.DateField(null=True, blank=True)
    historia = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    telefone = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to="clubs/logos/", null=True, blank=True)
    banner = models.ImageField(upload_to="clubs/banners/", null=True, blank=True)
    estadio = models.CharField(max_length=255, blank=True)
    cores = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = "Perfil de Clube"
        verbose_name_plural = "Perfis de Clubs"

    def __str__(self):
        return self.nome


class JogadorProfile(BaseModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="jogador_profile"
    )
    nome_completo = models.CharField(max_length=255)
    nome_desportivo = models.CharField(max_length=255, blank=True)
    data_nascimento = models.DateField(null=True, blank=True)
    nacionalidade = models.CharField(max_length=100, blank=True)
    altura = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    peso = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    pe_preferencial = models.CharField(max_length=20, blank=True)
    posicao = models.CharField(max_length=100, blank=True)
    foto = models.ImageField(upload_to="jogadores/fotos/", null=True, blank=True)
    biografia = models.TextField(blank=True)
    agente = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Perfil de Jogador"
        verbose_name_plural = "Perfis de Jogadores"

    def __str__(self):
        return self.nome_desportivo or self.nome_completo


class AdeptoProfile(BaseModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="adepto_profile"
    )
    nome = models.CharField(max_length=255)
    foto = models.ImageField(upload_to="adeptos/fotos/", null=True, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    pais = models.CharField(max_length=100, blank=True)
    clubs_favoritos = models.ManyToManyField(
        ClubeProfile,
        blank=True,
        related_name="seguidores"
    )
    jogadores_favoritos = models.ManyToManyField(
        JogadorProfile,
        blank=True,
        related_name="seguidores"
    )

    class Meta:
        verbose_name = "Perfil de Adepto"
        verbose_name_plural = "Perfis de Adeptos"

    def __str__(self):
        return self.nome
