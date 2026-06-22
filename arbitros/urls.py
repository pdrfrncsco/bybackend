from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RefereeViewSet, RefereeAvailabilityViewSet


router = DefaultRouter()
router.register(r'availability', RefereeAvailabilityViewSet, basename='referee-availability')
router.register(r'', RefereeViewSet, basename='referee')

urlpatterns = [
    path('', include(router.urls)),
]

