from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClubViewSet, ClubHistoryViewSet, StaffViewSet

router = DefaultRouter()
router.register(r'staff', StaffViewSet, basename='staff')
router.register(r'history', ClubHistoryViewSet, basename='club-history')
router.register(r'', ClubViewSet, basename='club')

urlpatterns = [
    path('', include(router.urls)),
]
