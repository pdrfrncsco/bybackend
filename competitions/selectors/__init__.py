from core.models import Tenant
from competitions.models import Competition


class CompetitionSelector:
    @staticmethod
    def list_for_tenant(*, tenant: Tenant) -> list[Competition]:
        return list(
            Competition.objects.filter(tenant=tenant).order_by("-created_at")
        )

    @staticmethod
    def get_by_id(*, tenant: Tenant, competition_id) -> Competition | None:
        try:
            return Competition.objects.get(id=competition_id, tenant=tenant)
        except Competition.DoesNotExist:
            return None
