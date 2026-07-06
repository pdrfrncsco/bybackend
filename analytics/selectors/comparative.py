"""
BOLAYETU — Analytics Comparative Selector

Provides period-over-period comparison for KPI metrics.
"""

from datetime import timedelta

from django.utils import timezone

from analytics.selectors.dashboard import DashboardAnalyticsSelector


class ComparativeAnalyticsSelector:
    """
    Compares KPI metrics across two time periods to compute deltas and trends.
    """

    SUPPORTED_PERIODS = ["7d", "30d", "90d", "365d"]

    @classmethod
    def compare(
        cls,
        *,
        tenant=None,
        competition=None,
        club=None,
        period: str = "30d",
    ) -> dict:
        """
        Compare KPIs for the current period vs the previous equivalent period.

        Returns a dict with current, previous, and delta for each metric.
        """
        if period not in cls.SUPPORTED_PERIODS:
            period = "30d"

        days = DashboardAnalyticsSelector.PERIOD_DAY_MAP.get(period, 30)
        today = timezone.localdate()

        current_start = today - timedelta(days=days)
        current_end = today

        previous_start = current_start - timedelta(days=days)
        previous_end = current_start - timedelta(days=1)

        current = DashboardAnalyticsSelector.get_overview(
            tenant=tenant,
            competition=competition,
            club=club,
            start_date=current_start,
            end_date=current_end,
        )
        previous = DashboardAnalyticsSelector.get_overview(
            tenant=tenant,
            competition=competition,
            club=club,
            start_date=previous_start,
            end_date=previous_end,
        )

        current_kpis = current.get("kpis", {})
        previous_kpis = previous.get("kpis", {})

        comparison = {}
        for key, current_value in current_kpis.items():
            prev_value = previous_kpis.get(key, 0)
            try:
                c = float(current_value)
                p = float(prev_value)
            except (TypeError, ValueError):
                c, p = 0.0, 0.0

            if p != 0:
                change_pct = round(((c - p) / abs(p)) * 100, 2)
            elif c > 0:
                change_pct = 100.0
            else:
                change_pct = 0.0

            comparison[key] = {
                "current": current_value,
                "previous": prev_value,
                "delta": round(c - p, 2),
                "change_pct": change_pct,
                "trend": "up" if c > p else ("down" if c < p else "stable"),
            }

        return {
            "period": period,
            "current_range": {
                "start": str(current_start),
                "end": str(current_end),
            },
            "previous_range": {
                "start": str(previous_start),
                "end": str(previous_end),
            },
            "comparison": comparison,
            "current_tournaments": current.get("tournaments", []),
            "current_top_clubs": current.get("top_clubs_by_players", []),
            "current_top_scorers": current.get("top_scorers", []),
        }
