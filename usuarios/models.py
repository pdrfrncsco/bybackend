from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q
from core.models import BaseModel, Tenant
from accounts.models import UserRole


class User(AbstractUser, BaseModel):
    name = models.CharField(max_length=255, blank=True)
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.ADEPTO)
    tenant = models.ForeignKey(Tenant, on_delete=models.SET_NULL, related_name='users', null=True, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    subscriptions = models.ManyToManyField(Tenant, related_name='subscribers', blank=True)

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email or self.username

    def get_roles_for_tenant(self, tenant=None):
        qs = self.role_assignments.select_related('role')
        if tenant is None:
            qs = qs.filter(tenant__isnull=True)
        else:
            qs = qs.filter(Q(tenant=tenant) | Q(tenant__isnull=True))
        return [assignment.role for assignment in qs]

    def has_role(self, slug, tenant=None):
        roles = self.get_roles_for_tenant(tenant)
        return any(role.slug == slug for role in roles)

    def has_permission(self, code, tenant=None):
        if not self.is_authenticated:
            return False
        if self.is_superuser or self.role == 'superadmin':
            return True
        if tenant is None:
            tenant = getattr(self, 'tenant', None)
        roles = self.get_roles_for_tenant(tenant)
        for role in roles:
            if role.permissions.filter(code=code).exists():
                return True
        return False


class Permission(BaseModel):
    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    module = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = 'Permission'
        verbose_name_plural = 'Permissions'

    def __str__(self):
        return self.code


class Role(BaseModel):
    LEVEL_CHOICES = (
        ('platform', 'Platform'),
        ('tenant', 'Tenant'),
    )
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='tenant')
    permissions = models.ManyToManyField(Permission, related_name='roles', blank=True)

    class Meta:
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'

    def __str__(self):
        return self.name


class UserRoleAssignment(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='role_assignments')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='user_assignments')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True, related_name='role_assignments')

    class Meta:
        verbose_name = 'User Role Assignment'
        verbose_name_plural = 'User Role Assignments'
        unique_together = ('user', 'role', 'tenant')

    def __str__(self):
        if self.tenant:
            return f'{self.user} - {self.role} ({self.tenant})'
        return f'{self.user} - {self.role} (platform)'


class AdminActionLog(BaseModel):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='admin_logs')
    tenant = models.ForeignKey(Tenant, on_delete=models.SET_NULL, null=True, blank=True, related_name='admin_logs')
    action = models.CharField(max_length=255)
    module = models.CharField(max_length=100, blank=True)
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        verbose_name = 'Admin Action Log'
        verbose_name_plural = 'Admin Action Logs'

    def __str__(self):
        return f'{self.action} by {self.user} at {self.created_at}'
