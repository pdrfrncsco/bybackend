from decimal import Decimal

from django.core.management.base import BaseCommand

from assinaturas.models import SubscriptionPlan


class Command(BaseCommand):
    help = "Gera planos de subscrição padrão para a plataforma"

    def handle(self, *args, **options):
        plans_data = [
            {
                "code": "TENANT_FREE",
                "name": "Free",
                "description": "Plano gratuito para organizações em fase inicial.",
                "target_type": "tenant",
                "plan_type": "free",
                "price_amount": Decimal("0.00"),
                "billing_period": "monthly",
                "is_active": True,
                "max_active_tournaments": 1,
                "max_clubs": 2,
                "max_players": 50,
                "max_news_articles": 10,
                "max_followers": 500,
                "organizer_commission_percent": Decimal("0.00"),
            },
            {
                "code": "TENANT_BASIC_MONTHLY",
                "name": "Basic Mensal",
                "description": "Plano básico para organizações com campeonatos regulares.",
                "target_type": "tenant",
                "plan_type": "basic",
                "price_amount": Decimal("15000.00"),
                "billing_period": "monthly",
                "is_active": True,
                "max_active_tournaments": 3,
                "max_clubs": 8,
                "max_players": 200,
                "max_news_articles": 50,
                "max_followers": 5000,
                "organizer_commission_percent": Decimal("0.00"),
            },
            {
                "code": "TENANT_PRO_MONTHLY",
                "name": "Pro Mensal",
                "description": "Plano profissional para ligas e federações activas.",
                "target_type": "tenant",
                "plan_type": "pro",
                "price_amount": Decimal("35000.00"),
                "billing_period": "monthly",
                "is_active": True,
                "max_active_tournaments": 8,
                "max_clubs": 24,
                "max_players": 800,
                "max_news_articles": 200,
                "max_followers": 25000,
                "organizer_commission_percent": Decimal("5.00"),
            },
            {
                "code": "TENANT_PREMIUM_YEARLY",
                "name": "Premium Anual",
                "description": "Plano premium anual com maior escala e benefícios.",
                "target_type": "tenant",
                "plan_type": "premium",
                "price_amount": Decimal("360000.00"),
                "billing_period": "yearly",
                "is_active": True,
                "max_active_tournaments": 20,
                "max_clubs": 64,
                "max_players": 5000,
                "max_news_articles": 1000,
                "max_followers": 100000,
                "organizer_commission_percent": Decimal("10.00"),
            },
            {
                "code": "FAN_FREEMIUM",
                "name": "Adepto Free",
                "description": "Plano gratuito para adeptos acompanharem competições e clubs.",
                "target_type": "fan",
                "plan_type": "freemium",
                "price_amount": Decimal("0.00"),
                "billing_period": "monthly",
                "is_active": True,
                "max_active_tournaments": None,
                "max_clubs": None,
                "max_players": None,
                "max_news_articles": None,
                "max_followers": None,
                "organizer_commission_percent": Decimal("0.00"),
            },
            {
                "code": "FAN_PREMIUM_MONTHLY",
                "name": "Adepto Premium Mensal",
                "description": "Plano premium para adeptos com acesso avançado a conteúdos.",
                "target_type": "fan",
                "plan_type": "premium",
                "price_amount": Decimal("1500.00"),
                "billing_period": "monthly",
                "is_active": True,
                "max_active_tournaments": None,
                "max_clubs": None,
                "max_players": None,
                "max_news_articles": None,
                "max_followers": None,
                "organizer_commission_percent": Decimal("0.00"),
            },
        ]

        created_count = 0
        updated_count = 0

        for data in plans_data:
            code = data["code"]
            defaults = {
                "name": data["name"],
                "description": data["description"],
                "target_type": data["target_type"],
                "plan_type": data["plan_type"],
                "price_amount": data["price_amount"],
                "currency": "AOA",
                "billing_period": data["billing_period"],
                "is_active": data["is_active"],
                "max_active_tournaments": data["max_active_tournaments"],
                "max_clubs": data["max_clubs"],
                "max_players": data["max_players"],
                "max_news_articles": data["max_news_articles"],
                "max_followers": data["max_followers"],
                "organizer_commission_percent": data["organizer_commission_percent"],
            }
            plan, created = SubscriptionPlan.objects.update_or_create(
                code=code,
                defaults=defaults,
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Planos de subscrição gerados com sucesso. Criados: {created_count}, Actualizados: {updated_count}."
            )
        )

