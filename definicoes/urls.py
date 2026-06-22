from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TenantSettingsViewSet


router = DefaultRouter()
router.register(r'', TenantSettingsViewSet, basename='tenant-settings')

urlpatterns = [
    path('', include(router.urls)),
]

