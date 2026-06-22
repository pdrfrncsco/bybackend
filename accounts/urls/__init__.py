from django.urls import path, include
from .profiles import urlpatterns as profiles_urls

urlpatterns = [
    path('', include(profiles_urls)),
]
