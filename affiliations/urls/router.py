from rest_framework.routers import DefaultRouter
from affiliations.views import (
    ClubeOrganizacaoRequestViewSet,
    JogadorClubeRequestViewSet,
    JogadorHistoricoClubeViewSet,
)

router = DefaultRouter()
router.register('clube-organizacao', ClubeOrganizacaoRequestViewSet, basename='clube-organizacao-request')
router.register('jogador-clube', JogadorClubeRequestViewSet, basename='jogador-clube-request')
router.register('historico', JogadorHistoricoClubeViewSet, basename='jogador-historico-clube')

urlpatterns = router.urls
