from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NewsArticleViewSet, PublicNewsViewSet

router = DefaultRouter()
router.register(r'articles', NewsArticleViewSet, basename='news-article')
router.register(r'public', PublicNewsViewSet, basename='public-news')

urlpatterns = [
    path('', include(router.urls)),
]
