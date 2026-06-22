from django.db import transaction
from accounts.models import (
    UserRole,
    OrganizacaoProfile,
    ClubeProfile,
    JogadorProfile,
    AdeptoProfile,
)


@transaction.atomic
def create_organizacao_profile(user, **data) -> OrganizacaoProfile:
    """
    Cria um perfil de organização e atualiza a role do utilizador.
    """
    # Garantir a role correta
    if user.role != UserRole.ORGANIZACAO:
        user.role = UserRole.ORGANIZACAO
        user.save(update_fields=['role'])
    
    # Criar ou obter o perfil
    profile, created = OrganizacaoProfile.objects.get_or_create(
        user=user,
        defaults=data
    )
    if not created:
        for key, value in data.items():
            setattr(profile, key, value)
        profile.save()
    return profile


@transaction.atomic
def create_clube_profile(user, **data) -> ClubeProfile:
    """
    Cria um perfil de clube e atualiza a role do utilizador.
    """
    if user.role != UserRole.CLUBE:
        user.role = UserRole.CLUBE
        user.save(update_fields=['role'])
    
    profile, created = ClubeProfile.objects.get_or_create(
        user=user,
        defaults=data
    )
    if not created:
        for key, value in data.items():
            setattr(profile, key, value)
        profile.save()
    return profile


@transaction.atomic
def create_jogador_profile(user, **data) -> JogadorProfile:
    """
    Cria um perfil de jogador e atualiza a role do utilizador.
    """
    if user.role != UserRole.JOGADOR:
        user.role = UserRole.JOGADOR
        user.save(update_fields=['role'])
    
    profile, created = JogadorProfile.objects.get_or_create(
        user=user,
        defaults=data
    )
    if not created:
        for key, value in data.items():
            setattr(profile, key, value)
        profile.save()
    return profile


@transaction.atomic
def create_adepto_profile(user, **data) -> AdeptoProfile:
    """
    Cria um perfil de adepto e atualiza a role do utilizador.
    """
    if user.role != UserRole.ADEPTO:
        user.role = UserRole.ADEPTO
        user.save(update_fields=['role'])
    
    # Many-to-many fields should not be in defaults during get_or_create
    clubes_favoritos = data.pop('clubes_favoritos', [])
    jogadores_favoritos = data.pop('jogadores_favoritos', [])

    profile, created = AdeptoProfile.objects.get_or_create(
        user=user,
        defaults=data
    )
    if not created:
        for key, value in data.items():
            setattr(profile, key, value)
        profile.save()
    
    if clubes_favoritos:
        profile.clubes_favoritos.set(clubes_favoritos)
    if jogadores_favoritos:
        profile.jogadores_favoritos.set(jogadores_favoritos)
        
    return profile
