from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('usuarios.urls')),
    path('api/accounts/', include('accounts.urls')),
    path('api/affiliations/', include('affiliations.urls')),
    path('api/clubs/', include('clubes.urls')),
    path('api/players/', include('jogadores.urls')),
    path('api/referees/', include('arbitros.urls')),
    path('api/matches/', include('partidas.urls')),
    path('api/treinadores/', include('treinadores.urls')),
    path('api/onboarding/', include('onboarding.urls')),
    path('api/tournaments/', include('torneios.urls')),
    path('api/classificacoes/', include('classificacoes.urls')),
    path('api/matchengine/', include('matchengine.urls')),
    path('api/stadiums/', include('estadios.urls')),
    path('api/dashboard/', include('dashboard.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/organizations/', include('organizacoes.urls')),
    path('api/fanportal/', include('fanportal.urls')),
    path('api/news/', include('news.urls')),
    path('api/ads/', include('ads.urls')),
    path('api/subscriptions/', include('assinaturas.urls')),
    path('api/reports/', include('relatorios.urls')),
    path('api/definicoes/', include('definicoes.urls')),
    path('api/referees/', include('arbitros.urls')),
    path('api/public/', include('publico.urls')),
    
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
