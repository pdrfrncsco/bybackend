from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PlayerViewSet, PlayerHistoryViewSet

router = DefaultRouter()
router.register(r'', PlayerViewSet, basename='player')
router.register(r'history', PlayerHistoryViewSet, basename='player-history')

urlpatterns = [
    path('', include(router.urls)),
]
