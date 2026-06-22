from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StadiumViewSet

router = DefaultRouter()
router.register(r'', StadiumViewSet, basename='stadium')

urlpatterns = [
    path('', include(router.urls)),
]
