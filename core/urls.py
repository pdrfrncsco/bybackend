"""
BOLAYETU — Core URLs
"""

from django.urls import path

from core.views.health import HealthView, LivenessView, ReadinessView

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("health/liveness/", LivenessView.as_view(), name="health-liveness"),
    path("health/readiness/", ReadinessView.as_view(), name="health-readiness"),
]
