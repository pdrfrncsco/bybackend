import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="analytics.generate_report_task",
)
def generate_report_task(self, report_id: str) -> dict:
    """
    Asynchronously generate a report by ID.
    """
    from analytics.services.report_service import ReportService

    logger.info("Starting report generation task for report: %s", report_id)
    try:
        ReportService.generate_report(report_id)
        return {"report_id": report_id, "status": "success"}
    except Exception as exc:
        logger.exception("Failed to generate report %s", report_id)
        raise self.retry(exc=exc)


@shared_task(
    name="analytics.snapshot_kpis_daily_task",
)
def snapshot_kpis_daily_task() -> dict:
    """
    Periodic task to snapshot KPIs for all tenants.
    """
    from analytics.services.kpi_service import KPIService

    today = timezone.localdate()
    logger.info("Starting periodic KPI snapshot for date: %s", today)
    try:
        KPIService.snapshot_all_tenants(snapshot_date=today)
        return {"date": str(today), "status": "success"}
    except Exception as exc:
        logger.exception("Failed to perform daily KPI snapshot")
        return {"error": str(exc), "status": "failed"}
