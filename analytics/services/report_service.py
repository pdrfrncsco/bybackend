import logging
from analytics.models import GeneratedReport
from analytics.constants import ReportType, ReportStatus, ReportFormat
from analytics.selectors import DashboardAnalyticsSelector
from analytics.services.export_service import ExportService

logger = logging.getLogger(__name__)


class ReportService:
    """
    Service for managing and generating system reports.
    """

    @classmethod
    def request_report(
        cls,
        *,
        tenant=None,
        name: str,
        report_type: str,
        format: str,
        filters: dict,
        created_by=None,
    ) -> GeneratedReport:
        """
        Create a report request in PENDING state and trigger its async generation.
        """
        report = GeneratedReport.objects.create(
            tenant=tenant,
            name=name,
            report_type=report_type,
            format=format,
            filters=filters,
            created_by=created_by,
            status=ReportStatus.PENDING,
        )

        try:
            from analytics.tasks import generate_report_task

            generate_report_task.delay(str(report.id))
        except Exception as exc:
            logger.exception("Failed to queue report generation task, running synchronously: %s", exc)
            # Run synchronously as fallback (e.g. if Redis/Celery is down or in testing without eager)
            cls.generate_report(str(report.id))

        return report

    @classmethod
    def generate_report(cls, report_id: str) -> None:
        """
        Perform the actual report generation.
        """
        try:
            report = GeneratedReport.objects.get(id=report_id)
        except GeneratedReport.DoesNotExist:
            logger.error("Report %s not found for generation.", report_id)
            return

        report.status = ReportStatus.PROCESSING
        report.save(update_fields=["status"])

        try:
            filters = report.filters or {}
            tenant = report.tenant

            competition = None
            competition_id = filters.get("competition_id")
            if competition_id:
                from competitions.models import Competition

                competition_queryset = Competition.objects.all()
                if tenant:
                    competition_queryset = competition_queryset.filter(tenant=tenant)
                competition = competition_queryset.filter(id=competition_id).first()

            club = None
            club_id = filters.get("club_id")
            if club_id:
                from clubs.models import Club

                club_queryset = Club.objects.all()
                if tenant:
                    club_queryset = club_queryset.filter(tenant=tenant)
                club = club_queryset.filter(id=club_id).first()

            period = filters.get("period", "all")
            start_date = filters.get("start_date")
            end_date = filters.get("end_date")

            payload = DashboardAnalyticsSelector.get_overview(
                tenant=tenant,
                competition=competition,
                club=club,
                period=period,
                start_date=start_date,
                end_date=end_date,
            )

            kpis = payload.get("kpis", {})
            data = []
            headers = ["Métrica", "Valor"]

            if report.report_type == ReportType.CLUB_OVERVIEW:
                data = [
                    {"Métrica": "Clube", "Valor": club.name if club else "N/A"},
                    {"Métrica": "Total Jogadores", "Valor": kpis.get("total_players", 0)},
                    {"Métrica": "Total Golos", "Valor": kpis.get("goals_total", 0)},
                    {"Métrica": "Média Golos por Jogo", "Valor": kpis.get("avg_goals_per_match", 0.0)},
                    {"Métrica": "Jogos Realizados", "Valor": kpis.get("matches_finished", 0)},
                    {"Métrica": "Jogos Agendados", "Valor": kpis.get("matches_scheduled", 0)},
                ]
            elif report.report_type == ReportType.COMPETITION_SUMMARY:
                data = [
                    {"Métrica": "Competição", "Valor": competition.name if competition else "N/A"},
                    {"Métrica": "Clubes Participantes", "Valor": kpis.get("total_clubs", 0)},
                    {"Métrica": "Total Jogadores Inscritos", "Valor": kpis.get("total_players", 0)},
                    {"Métrica": "Total Golos Marcados", "Valor": kpis.get("goals_total", 0)},
                    {"Métrica": "Média Golos por Jogo", "Valor": kpis.get("avg_goals_per_match", 0.0)},
                    {"Métrica": "Jogos Concluídos", "Valor": kpis.get("matches_finished", 0)},
                    {"Métrica": "Jogos Agendados", "Valor": kpis.get("matches_scheduled", 0)},
                    {"Métrica": "Jogos ao Vivo", "Valor": kpis.get("matches_live", 0)},
                ]
            elif report.report_type == ReportType.ORGANIZATION_PERFORMANCE:
                data = [
                    {"Métrica": "Total Clubes Filiados", "Valor": kpis.get("total_clubs", 0)},
                    {"Métrica": "Total Jogadores", "Valor": kpis.get("total_players", 0)},
                    {"Métrica": "Torneios Ativos", "Valor": kpis.get("active_tournaments", 0)},
                    {"Métrica": "Torneios Concluídos", "Valor": kpis.get("tournaments_completed", 0)},
                    {"Métrica": "Jogos Realizados", "Valor": kpis.get("matches_finished", 0)},
                    {"Métrica": "Subscritores", "Valor": kpis.get("organization_subscribers", 0)},
                ]
            elif report.report_type == ReportType.FINANCIAL_SUMMARY:
                data = [
                    {"Métrica": "Subscritores Ativos", "Valor": kpis.get("organization_subscribers", 0)},
                    {"Métrica": "Receita Total", "Valor": kpis.get("total_revenue", 0)},
                    {"Métrica": "Média Subscritores por Torneio", "Valor": kpis.get("avg_subscribers_per_tournament", 0.0)},
                ]

            # Format report data
            content_file = ExportService.export_data(data, headers, report.format)
            filename = f"report_{report_id}.{report.format}"
            content_file.name = filename

            # Upload using media assets service
            from media_assets.services.media_service import MediaAssetService
            from media_assets.constants import OwnerType, AssetCategory

            asset = MediaAssetService.upload_for_owner(
                file=content_file,
                owner_type=OwnerType.SYSTEM,
                owner_id=report.id,
                role=AssetCategory.DOCUMENT,
                name=report.name,
                tenant=tenant,
                uploaded_by=report.created_by,
            )

            report.file = asset
            report.status = ReportStatus.COMPLETED
            report.error_message = None
            report.save(update_fields=["file", "status", "error_message"])
            logger.info("Report %s generated successfully.", report_id)

        except Exception as exc:
            import traceback

            error_msg = f"{str(exc)}\n{traceback.format_exc()}"
            report.status = ReportStatus.FAILED
            report.error_message = error_msg
            report.save(update_fields=["status", "error_message"])
            logger.error("Failed to generate report %s: %s", report_id, error_msg)
