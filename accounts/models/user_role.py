from django.db import models


class UserRole(models.TextChoices):
    # New sports profiles
    ADMIN = "ADMIN", "Administrador"
    ORGANIZACAO = "ORGANIZACAO", "Organização"
    CLUBE = "CLUBE", "Clube"
    JOGADOR = "JOGADOR", "Jogador"
    ADEPTO = "ADEPTO", "Adepto"
    
    # Backwards compatibility
    SUPERADMIN = "superadmin", "Super Admin"
    ADS_MANAGER = "ads_manager", "Ads Manager"
    LEGACY_ADMIN = "admin", "Tenant Admin"
    LEGACY_MANAGER = "manager", "Manager"
    LEGACY_VIEWER = "viewer", "Viewer"
