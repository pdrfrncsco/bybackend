from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView,
    CustomTokenObtainPairView,
    UserDetailView,
    ChangePasswordView,
    SetPasswordFromInviteView,
    ValidatePasswordView,
    TenantUserViewSet,
)

router = DefaultRouter()
router.register(r'users', TenantUserViewSet, basename='tenant-user')

urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='auth_login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', UserDetailView.as_view(), name='auth_me'),
    path('change-password/', ChangePasswordView.as_view(), name='auth_change_password'),
    path('set-password/', SetPasswordFromInviteView.as_view(), name='auth_set_password'),
    path('validate-password/', ValidatePasswordView.as_view(), name='auth_validate_password'),
    path('', include(router.urls)),
]
