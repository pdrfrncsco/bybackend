from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ReportJobViewSet


router = DefaultRouter()
router.register(r"", ReportJobViewSet, basename="report-job")


urlpatterns = [
    path("", include(router.urls)),
]

