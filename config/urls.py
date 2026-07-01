"""
BOLAYETU — URL Configuration
Phase 1: Architecture, Authentication, Multi-Tenant
"""

from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),

    # API v1
    path('api/v1/auth/', include('accounts.urls')),
    path('api/v1/organizations/', include('organizations.urls')),
    path('api/v1/competitions/', include('competitions.urls')),
    path('api/v1/clubs/', include('clubs.urls')),
    path('api/v1/', include('core.urls')),

    # Phase 1 — Digital Asset Management (DAM)
    path('api/v1/media/', include('media_assets.urls')),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
