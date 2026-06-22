from rest_framework import serializers
from django.contrib.auth import get_user_model, password_validation
from django.utils.text import slugify
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from core.serializers import TenantSerializer
from core.models import Tenant
from assinaturas.models import Subscription

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    organization = TenantSerializer(source='tenant', read_only=True)
    subscribedOrganizationIds = serializers.PrimaryKeyRelatedField(
        source='subscriptions',
        many=True,
        read_only=True,
    )
    avatar_url = serializers.ImageField(source='avatar', read_only=True)
    hasActiveSubscription = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'name',
            'role',
            'organization',
            'avatar',
            'avatar_url',
            'subscribedOrganizationIds',
            'hasActiveSubscription',
        )
        extra_kwargs = {
            'id': {'read_only': True},
            'role': {'read_only': True},
            'username': {'read_only': True},
            'avatar': {'write_only': True, 'required': False, 'allow_null': True},
        }

    def get_hasActiveSubscription(self, obj):
        today = timezone.now().date()
        qs = Subscription.objects.filter(status__in=['active', 'pending']).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=today)
        )
        qs = qs.filter(start_date__lte=today)
        if obj.tenant:
            qs = qs.filter(subscriber_type='tenant', tenant=obj.tenant)
        else:
            qs = qs.filter(subscriber_type='fan', fan=obj)
        return qs.exists()


class TenantUserSerializer(serializers.ModelSerializer):
    avatar_url = serializers.ImageField(source='avatar', read_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'name',
            'role',
            'avatar_url',
        )
        read_only_fields = ('id', 'email')

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    tenant_name = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'name', 'role', 'tenant_name')

    def create(self, validated_data):
        tenant_name = validated_data.pop('tenant_name', None)
        from accounts.models import UserRole
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            name=validated_data.get('name', ''),
            role=validated_data.get('role', UserRole.ADEPTO)
        )

        if tenant_name:
            slug = slugify(tenant_name)
            if not slug:
                slug = "default"
            # Ensure unique slug
            original_slug = slug
            counter = 1
            while Tenant.objects.filter(slug=slug).exists():
                slug = f"{original_slug}-{counter}"
                counter += 1
                
            tenant = Tenant.objects.create(name=tenant_name, slug=slug)
            user.tenant = tenant
            user.save()

        return user


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        new_password = attrs.get('new_password') or ''
        confirm_password = attrs.get('confirm_password') or ''
        if new_password != confirm_password:
            raise serializers.ValidationError('As novas palavras-passe não coincidem.')
        if len(new_password) < 8:
            raise serializers.ValidationError('A nova palavra-passe deve ter pelo menos 8 caracteres.')
        return attrs


class SetPasswordFromInviteSerializer(serializers.Serializer):
    uid = serializers.CharField(write_only=True)
    token = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        uid = attrs.get('uid') or ''
        token = attrs.get('token') or ''
        new_password = attrs.get('new_password') or ''
        confirm_password = attrs.get('confirm_password') or ''

        if not uid or not token:
            raise serializers.ValidationError('Dados de convite inválidos.')

        if new_password != confirm_password:
            raise serializers.ValidationError('As novas palavras-passe não coincidem.')

        try:
            uid_int = urlsafe_base64_decode(uid).decode()
            user = User.objects.get(pk=uid_int)
        except Exception:
            raise serializers.ValidationError('Convite inválido.')

        if not default_token_generator.check_token(user, token):
            raise serializers.ValidationError('O link de convite é inválido ou expirou.')

        try:
            password_validation.validate_password(new_password, user=user)
        except serializers.ValidationError as e:
            raise serializers.ValidationError(e.detail)

        attrs['user'] = user
        return attrs

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['name'] = user.name
        token['role'] = user.role
        if user.tenant:
            token['tenant_id'] = str(user.tenant.id)
            token['tenant_slug'] = user.tenant.slug

        return token
