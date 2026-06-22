from django.urls import path, include
from .router import urlpatterns as router_urls

urlpatterns = [
    path('', include(router_urls)),
]
