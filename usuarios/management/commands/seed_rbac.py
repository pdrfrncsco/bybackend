from django.core.management.base import BaseCommand
from usuarios.models import Permission, Role


class Command(BaseCommand):
    help = "Seed de roles e permissões padrão para RBAC"

    def handle(self, *args, **options):
        permissions_data = [
            ("manage_platform", "Gerir plataforma", "Administração da plataforma", "platform"),
            ("manage_tenant_settings", "Gerir definições do tenant", "Configurações da organização", "tenant"),
            ("manage_team", "Gerir equipa", "Gestão de equipas e staff", "tenant"),
            ("manage_players", "Gerir jogadores", "Gestão de jogadores", "tenant"),
            ("manage_ads", "Gerir publicidade", "Gestão de anúncios e patrocínios", "platform"),
        ]

        permissions = {}
        for code, name, description, module in permissions_data:
            perm, _ = Permission.objects.get_or_create(
                code=code,
                defaults={
                    "name": name,
                    "description": description,
                    "module": module,
                },
            )
            permissions[code] = perm

        roles_data = [
            ("Superadmin", "superadmin", "platform", list(permissions.values())),
            (
                "Tenant Admin",
                "tenant_admin",
                "tenant",
                [
                    permissions["manage_tenant_settings"],
                    permissions["manage_team"],
                    permissions["manage_players"],
                    permissions["manage_ads"],
                ],
            ),
            (
                "Manager",
                "manager",
                "tenant",
                [
                    permissions["manage_team"],
                    permissions["manage_players"],
                ],
            ),
            (
                "Viewer",
                "viewer",
                "tenant",
                [],
            ),
            (
                "Ads Manager",
                "ads_manager",
                "platform",
                [
                    permissions["manage_ads"],
                ],
            ),
        ]

        for name, slug, level, perms in roles_data:
            role, _ = Role.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "level": level,
                },
            )
            role.permissions.set(perms)

        self.stdout.write(self.style.SUCCESS("RBAC seed executado com sucesso"))

