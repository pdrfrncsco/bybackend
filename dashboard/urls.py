from django.urls import path
from .views import DashboardOverviewView, PublicStatsView

urlpatterns = [
    path('overview/', DashboardOverviewView.as_view(), name='dashboard-overview'),
    path('public-stats/', PublicStatsView.as_view(), name='dashboard-public-stats'),
]

