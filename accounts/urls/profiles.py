from rest_framework.routers import DefaultRouter
from accounts.views import (
    OrganizacaoProfileViewSet,
    ClubeProfileViewSet,
    JogadorProfileViewSet,
    AdeptoProfileViewSet,
)

router = DefaultRouter()
router.register('organizacoes', OrganizacaoProfileViewSet, basename='organizacao-profile')
router.register('clubs', ClubeProfileViewSet, basename='clube-profile')
router.register('jogadores', JogadorProfileViewSet, basename='jogador-profile')
router.register('adeptos', AdeptoProfileViewSet, basename='adepto-profile')

urlpatterns = router.urls
