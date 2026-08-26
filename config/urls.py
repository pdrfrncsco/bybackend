"""
BOLAYETU — URL Configuration
Phase 1: Architecture, Authentication, Multi-Tenant
"""

from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    # API v1
    path("api/v1/auth/", include("accounts.urls")),
    path("api/v1/organizations/", include("organizations.urls")),
    path("api/v1/competitions/", include("competitions.urls")),
    path("api/v1/clubs/", include("clubs.urls")),
    path("api/v1/dashboard/", include("analytics.urls")),
    path("api/v1/", include("core.urls")),
    # Phase 1 — Digital Asset Management (DAM)
    path("api/v1/media/", include("media_assets.urls")),
    # Phase 1.5 — Notifications (Phase 5)
    path("api/v1/notifications/", include("notifications.urls")),
    # Phase 2 — Players (Global Domain)
    path("api/v1/players/", include("players.urls")),
    # Phase 7 — Transfers
    path("api/v1/transfers/", include("transfers.urls")),
    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
