from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db import transaction
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils import timezone
from datetime import timedelta
from drf_spectacular.utils import extend_schema, extend_schema_view
from core.models import Tenant
from assinaturas.models import SubscriptionPlan, Subscription
from .models import OnboardingRequest
from .serializers import OnboardingRequestSerializer

User = get_user_model()

@extend_schema_view(
    create=extend_schema(
        tags=["Onboarding", "Public"],
        description="Submete um pedido de onboarding para criar uma nova organização."
    ),
    list=extend_schema(
        tags=["Onboarding"],
        description="Lista pedidos de onboarding. Normalmente usado apenas em contexto administrativo."
    ),
    retrieve=extend_schema(
        tags=["Onboarding"],
        description="Detalhes de um pedido de onboarding. Normalmente usado apenas em contexto administrativo."
    ),
)
class OnboardingViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = OnboardingRequest.objects.all()
    serializer_class = OnboardingRequestSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def create(self, request, *args, **kwargs):
        # Custom creation logic if needed, e.g., validation
        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    @extend_schema(
        tags=["Onboarding"],
        description="Finaliza o onboarding: cria Tenant e utilizador administrador com base nos dados submetidos."
    )
    def complete(self, request, pk=None):
        """
        Finalize onboarding: Create actual Tenant/Organization and User.
        """
        onboarding = self.get_object()
        if onboarding.status == 'completed':
             return Response({'detail': 'Onboarding already completed'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get user data from request
        admin_email = request.data.get('admin_email')
        admin_name = request.data.get('admin_name')
        password = request.data.get('password')
        
        if not admin_email or not password:
            return Response({'detail': 'Email e password são obrigatórios'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_email(admin_email)
        except ValidationError:
            return Response({'detail': 'Email inválido.'}, status=status.HTTP_400_BAD_REQUEST)

        if admin_name is not None and isinstance(admin_name, str) and not admin_name.strip():
            return Response({'detail': 'Nome é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_password(password)
        except ValidationError as e:
            msg = e.messages[0] if getattr(e, "messages", None) else "Password inválida."
            return Response({'detail': msg}, status=status.HTTP_400_BAD_REQUEST)

        if Tenant.objects.filter(slug=onboarding.organization_slug).exists():
            return Response({'detail': 'Este slug já está em uso.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # 1. Create Tenant
                tenant = Tenant.objects.create(
                    name=onboarding.organization_name,
                    slug=onboarding.organization_slug,
                    primary_color=onboarding.primary_color,
                    type=onboarding.organization_type,
                    country=onboarding.country,
                )
                if onboarding.logo:
                    tenant.logo = onboarding.logo
                    tenant.save()

                # 2. Create User
                if User.objects.filter(email=admin_email).exists():
                    return Response({'detail': 'Este email já está registado.'}, status=status.HTTP_400_BAD_REQUEST)

                user = User.objects.create_user(
                    username=admin_email,
                    email=admin_email,
                    password=password,
                    name=admin_name,
                    role='admin',
                    tenant=tenant
                )

                plan = SubscriptionPlan.objects.filter(code="TENANT_PRO_MONTHLY", is_active=True).first()
                if not plan:
                    plan = SubscriptionPlan.objects.filter(
                        target_type="tenant",
                        plan_type="pro",
                        billing_period="monthly",
                        is_active=True,
                    ).first()
                if not plan:
                    plan = SubscriptionPlan.objects.filter(code="TENANT_FREE", is_active=True).first()

                if not plan:
                    raise Exception("Plano de subscrição não encontrado.")

                today = timezone.now().date()
                trial_end = today + timedelta(days=30) if plan.plan_type == "pro" else None
                Subscription.objects.create(
                    subscriber_type="tenant",
                    tenant=tenant,
                    plan=plan,
                    start_date=today,
                    end_date=trial_end,
                    status="active",
                    payment_method="none",
                    billing_period=plan.billing_period,
                )
                
                # 3. Mark Onboarding as completed
                onboarding.status = 'completed'
                onboarding.save()
                
                # 4. Generate Tokens (Optional, but good for auto-login)
                # For now, frontend calls login separately, so just return success
                
                return Response(
                    {
                        'status': 'completed',
                        'detail': f'Organização, conta e plano {plan.name} ativados com sucesso!',
                        'trial_ends_at': str(trial_end) if trial_end else None,
                        'plan_code': plan.code,
                    }
                )
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
