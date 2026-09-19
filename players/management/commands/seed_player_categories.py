"""
BOLAYETU — Seed Player Categories Command

Populates default official federation categories for tenants.
"""

from django.core.management.base import BaseCommand
from core.models import Tenant
from players.models.category import PlayerCategory

DEFAULT_CATEGORIES = [
    {"name": "Petiz", "slug": "petiz", "min_age": 7, "max_age": 9, "display_order": 1, "gender": "mixed"},
    {"name": "Traquina", "slug": "traquina", "min_age": 9, "max_age": 11, "display_order": 2, "gender": "mixed"},
    {"name": "Benjamim", "slug": "benjamim", "min_age": 11, "max_age": 13, "display_order": 3, "gender": "mixed"},
    {"name": "Infantil", "slug": "infantil", "min_age": 13, "max_age": 15, "display_order": 4, "gender": "mixed"},
    {"name": "Iniciado", "slug": "iniciado", "min_age": 15, "max_age": 17, "display_order": 5, "gender": "mixed"},
    {"name": "Juvenil", "slug": "juvenil", "min_age": 17, "max_age": 19, "display_order": 6, "gender": "mixed"},
    {"name": "Júnior", "slug": "junior", "min_age": 19, "max_age": 23, "display_order": 7, "gender": "mixed"},
    {"name": "Sénior", "slug": "senior", "min_age": 16, "max_age": None, "display_order": 8, "gender": "mixed"},
    {"name": "Veterano", "slug": "veterano", "min_age": 35, "max_age": None, "display_order": 9, "gender": "mixed"},
]


class Command(BaseCommand):
    help = "Seed default federation player categories for existing tenants"

    def add_arguments(self, parser):
        parser.add_argument(
            "--tenant",
            type=str,
            help="Tenant slug or ID to seed specifically. If omitted, seeds all tenants.",
        )

    def handle(self, *args, **options):
        tenant_filter = options.get("tenant")
        if tenant_filter:
            tenants = Tenant.objects.filter(slug=tenant_filter)
            if not tenants.exists():
                tenants = Tenant.objects.filter(id=tenant_filter)
        else:
            tenants = Tenant.objects.all()

        if not tenants.exists():
            self.stdout.write(self.style.WARNING("No tenants found to seed categories for."))
            return

        total_created = 0
        for tenant in tenants:
            self.stdout.write(f"Seeding categories for tenant: {tenant.name}...")
            for cat_data in DEFAULT_CATEGORIES:
                obj, created = PlayerCategory.objects.get_or_create(
                    tenant=tenant,
                    club=None,
                    slug=cat_data["slug"],
                    defaults={
                        "name": cat_data["name"],
                        "min_age": cat_data["min_age"],
                        "max_age": cat_data["max_age"],
                        "gender": cat_data["gender"],
                        "display_order": cat_data["display_order"],
                        "scope": PlayerCategory.Scope.FEDERATION,
                        "is_custom": False,
                        "is_active": True,
                    },
                )
                if created:
                    total_created += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {total_created} player categories."))
