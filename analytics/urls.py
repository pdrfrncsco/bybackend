from django.urls import path

from analytics.views import (
    DashboardOverviewView,
    PublicStatsView,
    OrganizationDashboardView,
    ClubDashboardView,
    CompetitionDashboardView,
    GeneratedReportListCreateView,
    GeneratedReportDetailView,
)

urlpatterns = [
    path("overview/", DashboardOverviewView.as_view(), name="dashboard-overview"),
    path("public-stats/", PublicStatsView.as_view(), name="dashboard-public-stats"),
    path("dashboard/organization/", OrganizationDashboardView.as_view(), name="dashboard-organization"),
    path("dashboard/club/<uuid:club_id>/", ClubDashboardView.as_view(), name="dashboard-club"),
    path("dashboard/competition/<uuid:competition_id>/", CompetitionDashboardView.as_view(), name="dashboard-competition"),
    path("reports/", GeneratedReportListCreateView.as_view(), name="report-list-create"),
    path("reports/<uuid:pk>/", GeneratedReportDetailView.as_view(), name="report-detail"),
]
