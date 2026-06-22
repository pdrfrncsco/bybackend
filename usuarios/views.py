from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework.exceptions import PermissionDenied
from django.conf import settings
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.utils.crypto import get_random_string
from drf_spectacular.utils import extend_schema, extend_schema_view
import logging
from .models import AdminActionLog
from core.permissions import HasPermission
from .serializers import (
    RegisterSerializer,
    UserSerializer,
    CustomTokenObtainPairSerializer,
    ChangePasswordSerializer,
    TenantUserSerializer,
    SetPasswordFromInviteSerializer,
)

User = get_user_model()
logger = logging.getLogger(__name__)

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class UserDetailView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user


class ChangePasswordView(generics.GenericAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        current_password = serializer.validated_data.get('current_password')
        if not user.check_password(current_password):
            return Response(
                {'detail': 'A palavra-passe atual está incorreta.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        new_password = serializer.validated_data.get('new_password')
        user.set_password(new_password)
        user.save()
        return Response({'detail': 'Palavra-passe atualizada com sucesso.'})


class SetPasswordFromInviteView(generics.GenericAPIView):
    serializer_class = SetPasswordFromInviteSerializer
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        new_password = serializer.validated_data['new_password']
        user.set_password(new_password)
        user.save()
        return Response({'detail': 'Palavra-passe definida com sucesso.'})


class ValidatePasswordView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        password = request.data.get('password') or ''
        email = request.data.get('email') or ''
        name = request.data.get('name') or ''

        if not password:
            return Response(
                {'valid': False, 'errors': ['Palavra-passe é obrigatória.']},
                status=status.HTTP_400_BAD_REQUEST,
            )

        temp_user = User(
            username=email or None,
            email=email or None,
            name=name or '',
        )

        try:
            validate_password(password, user=temp_user)
        except ValidationError as e:
            errors = list(getattr(e, 'messages', None) or [str(e)])
            return Response({'valid': False, 'errors': errors}, status=status.HTTP_200_OK)

        return Response({'valid': True, 'errors': []}, status=status.HTTP_200_OK)



@extend_schema_view(
    list=extend_schema(
        tags=["Users", "Admin Only"],
        description="Lista utilizadores activos do tenant actual (ou todos para SUPERADMIN). Requer utilizador autenticado com permissões de gestão.",
    ),
    retrieve=extend_schema(
        tags=["Users", "Admin Only"],
        description="Detalhes de utilizador. Requer utilizador autenticado com permissões de gestão."
    ),
    create=extend_schema(
        tags=["Users", "Admin Only"],
        description="Cria utilizador no tenant actual. Requer role ADMIN ou SUPERADMIN."
    ),
    update=extend_schema(
        tags=["Users", "Admin Only"],
        description="Actualiza utilizador (incluindo função). Requer role ADMIN ou SUPERADMIN."
    ),
    partial_update=extend_schema(
        tags=["Users", "Admin Only"],
        description="Actualiza parcialmente utilizador. Requer role ADMIN ou SUPERADMIN."
    ),
    destroy=extend_schema(
        tags=["Users", "Admin Only"],
        description="Desactiva utilizador. Requer role ADMIN ou SUPERADMIN."
    ),
)
class TenantUserViewSet(viewsets.ModelViewSet):
    serializer_class = TenantUserSerializer
    permission_classes = (permissions.IsAuthenticated, HasPermission)

    def get_queryset(self):
        user = self.request.user
        tenant = getattr(user, 'tenant', None)
        from accounts.models import UserRole
        is_superadmin = user.role in [UserRole.SUPERADMIN, 'superadmin'] or user.is_superuser
        if is_superadmin:
            return User.objects.filter(is_active=True)
        if tenant is None:
            return User.objects.none()
        return User.objects.filter(tenant=tenant, is_active=True)

    def perform_update(self, serializer):
        user = self.request.user
        from accounts.models import UserRole
        admin_roles = [UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.LEGACY_ADMIN, 'admin', 'superadmin']
        superadmin_roles = [UserRole.SUPERADMIN, 'superadmin']
        if user.role not in admin_roles and not user.is_superuser:
            raise PermissionDenied('Apenas administradores podem actualizar utilizadores.')
        instance = serializer.instance
        tenant = getattr(user, 'tenant', None)
        if user.role not in superadmin_roles and not user.is_superuser and tenant is not None and instance.tenant_id != tenant.id:
            raise PermissionDenied('Utilizador não pertence ao seu tenant.')
        if instance.id == user.id:
            raise PermissionDenied('Não é possível alterar a sua própria função.')
        previous_role = instance.role
        updated_user = serializer.save()
        AdminActionLog.objects.create(
            user=user,
            tenant=tenant,
            action='update_user_role',
            module='usuarios',
            details=f'Updated user {updated_user.id} role from {previous_role} to {updated_user.role}',
        )

    def perform_destroy(self, instance):
        user = self.request.user
        from accounts.models import UserRole
        admin_roles = [UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.LEGACY_ADMIN, 'admin', 'superadmin']
        superadmin_roles = [UserRole.SUPERADMIN, 'superadmin']
        if user.role not in admin_roles and not user.is_superuser:
            raise PermissionDenied('Apenas administradores podem remover utilizadores.')
        tenant = getattr(user, 'tenant', None)
        if user.role not in superadmin_roles and not user.is_superuser and tenant is not None and instance.tenant_id != tenant.id:
            raise PermissionDenied('Utilizador não pertence ao seu tenant.')
        if instance.id == user.id:
            raise PermissionDenied('Não é possível remover a sua própria conta.')
        instance.is_active = False
        instance.save()
        AdminActionLog.objects.create(
            user=user,
            tenant=tenant,
            action='deactivate_user',
            module='usuarios',
            details=f'Deactivated user {instance.id}',
        )

    def create(self, request, *args, **kwargs):
        user = request.user
        from accounts.models import UserRole
        admin_roles = [UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.LEGACY_ADMIN, 'admin', 'superadmin']
        if user.role not in admin_roles and not user.is_superuser:
            raise PermissionDenied('Apenas administradores podem criar utilizadores.')
        tenant = getattr(user, 'tenant', None)
        if tenant is None:
            raise PermissionDenied('Tenant não definido para o utilizador.')

        name = request.data.get('name') or ''
        email = request.data.get('email') or ''
        role = request.data.get('role') or 'viewer'

        if not email:
            return Response({'email': ['Este campo é obrigatório.']}, status=status.HTTP_400_BAD_REQUEST)

        if role not in ['admin', 'manager', 'viewer', UserRole.ADMIN, UserRole.ORGANIZACAO, UserRole.CLUBE, UserRole.JOGADOR, UserRole.ADEPTO]:
            return Response({'role': ['Função inválida.']}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email, tenant=tenant).exists():
            return Response({'email': ['Já existe um utilizador com este email neste tenant.']}, status=status.HTTP_400_BAD_REQUEST)

        password = get_random_string(16)
        new_user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            name=name,
            role=role,
            tenant=tenant,
        )

        try:
            token = default_token_generator.make_token(new_user)
            uid = urlsafe_base64_encode(force_bytes(new_user.pk))
            reset_url = f"{settings.FRONTEND_URL}/#/set-password?uid={uid}&token={token}"

            subject = "Convite para aceder ao BolaYetu"
            message = (
                f"Olá {name or email},\n\n"
                "Foi convidado para aceder ao portal BolaYetu.\n\n"
                "Para definir a sua palavra-passe e concluir o registo, aceda ao link abaixo:\n"
                f"{reset_url}\n\n"
                "Se não estava à espera deste email, pode simplesmente ignorá-lo.\n\n"
                "Obrigado."
            )

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=True,
            )
        except Exception:
            logger.error("Erro ao enviar email de convite para %s", email)

        serializer = self.get_serializer(new_user)
        headers = self.get_success_headers(serializer.data)
        AdminActionLog.objects.create(
            user=user,
            tenant=tenant,
            action='create_user',
            module='usuarios',
            details=f'Created user {new_user.id} with role {new_user.role}',
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
