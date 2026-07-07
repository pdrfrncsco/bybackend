from datetime import date
from django.utils import timezone
from analytics.models import KPISnapshot
from analytics.selectors import DashboardAnalyticsSelector
from analytics.constants import MetricKey
from core.models import Tenant


class KPIService:
    """
    Service for calculating and storing KPI Snapshots.
    """

    @classmethod
    def snapshot_kpis(cls, *, tenant: Tenant = None, snapshot_date: date = None) -> list[KPISnapshot]:
        if snapshot_date is None:
            snapshot_date = timezone.localdate()

        # Fetch the calculated KPIs from the Selector
        payload = DashboardAnalyticsSelector.get_overview(
            tenant=tenant,
            period="all",
        )
        kpis = payload.get("kpis", {})

        snapshots = []
        metric_mapping = {
            "total_clubs": MetricKey.TOTAL_CLUBS,
            "total_players": MetricKey.TOTAL_PLAYERS,
            "active_tournaments": MetricKey.ACTIVE_TOURNAMENTS,
            "total_matches": MetricKey.TOTAL_MATCHES,
            "matches_finished": MetricKey.MATCHES_FINISHED,
            "matches_scheduled": MetricKey.MATCHES_SCHEDULED,
            "matches_live": MetricKey.MATCHES_LIVE,
            "goals_total": MetricKey.GOALS_TOTAL,
            "avg_goals_per_match": MetricKey.AVG_GOALS_PER_MATCH,
            "organization_subscribers": MetricKey.ORGANIZATION_SUBSCRIBERS,
            "total_revenue": MetricKey.TOTAL_REVENUE,
            "players_this_month": MetricKey.PLAYERS_THIS_MONTH,
            "players_last_month": MetricKey.PLAYERS_LAST_MONTH,
        }

        for selector_key, metric_key in metric_mapping.items():
            value = kpis.get(selector_key, 0.0)
            try:
                value = float(value)
            except (ValueError, TypeError):
                value = 0.0

            snapshot, created = KPISnapshot.objects.update_or_create(
                tenant=tenant,
                date=snapshot_date,
                metric_key=metric_key,
                defaults={"value": value},
            )
            snapshots.append(snapshot)

        return snapshots

    @classmethod
    def snapshot_all_tenants(cls, *, snapshot_date: date = None) -> None:
        # Snapshot for system global (None tenant)
        cls.snapshot_kpis(tenant=None, snapshot_date=snapshot_date)
        # Snapshot for each active tenant
        for tenant in Tenant.objects.filter(status=Tenant.TenantStatus.ACTIVE):
            cls.snapshot_kpis(tenant=tenant, snapshot_date=snapshot_date)
