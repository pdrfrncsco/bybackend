from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MatchEngineViewSet

router = DefaultRouter()
router.register(r'matches', MatchEngineViewSet, basename='matchengine-match')

urlpatterns = [
    path('', include(router.urls)),
]

