from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TournamentViewSet, TournamentGroupViewSet, PublicTournamentViewSet

router = DefaultRouter()
router.register(r'public', PublicTournamentViewSet, basename='public-tournament')
router.register(r'groups', TournamentGroupViewSet, basename='tournament-group')
router.register(r'', TournamentViewSet, basename='tournament')

urlpatterns = [
    path('', include(router.urls)),
]
