"""
BOLAYETU — User Model

The User represents a GLOBAL identity in the Bolayetu platform.

Architecture principle (06A_GLOBAL_AND_TENANT_DOMAIN.md):
    The User does NOT belong to any Tenant.
    It represents a unique digital identity on the platform.

    Tenant membership is managed through the TenantMembership model.
    Business profiles (Organization, Club, Player, Fan) are separate models
    that reference the User via a One-to-One relationship.

Identity vs Profile separation:
    User (this model) → Authentication, Authorization, Security
    Profile models → Business context, permissions within a Tenant
"""

import uuid

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _

from accounts.constants import AccountStatus, LanguageCode, TimezoneDefault


class UserManager(BaseUserManager):
    """Custom manager that uses email as the unique identifier."""

    def create_user(
        self,
        email: str,
        password: str | None = None,
        **extra_fields,
    ) -> "User":
        """Create and save a standard user."""
        if not email:
            raise ValueError("Users must have an email address.")

        email = self.normalize_email(email)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email: str,
        password: str | None = None,
        **extra_fields,
    ) -> "User":
        """Create and save a superuser."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Global user identity model.

    Represents a unique digital identity on the Bolayetu platform.
    This model handles authentication, authorization and account settings.

    This model intentionally does NOT contain:
        - Tenant references (managed via TenantMembership)
        - Business profile data (managed via Organization, Club, Player, Fan models)
        - Uploaded files (managed via MediaAsset)
    """

    # Override AbstractUser fields
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID",
    )
    username = models.CharField(
        max_length=150,
        unique=True,
        null=True,
        blank=True,
        verbose_name="Username",
        help_text="Optional. Used for public profile URLs.",
    )
    email = models.EmailField(
        unique=True,
        verbose_name="Email Address",
    )
    first_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="First Name",
    )
    last_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Last Name",
    )

    # Contact
    phone = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="Phone Number",
    )

    # Account status
    status = models.CharField(
        max_length=30,
        choices=AccountStatus.CHOICES,
        default=AccountStatus.PENDING_VERIFICATION,
        verbose_name="Account Status",
    )
    is_email_verified = models.BooleanField(
        default=False,
        verbose_name="Email Verified",
    )

    # Preferences
    language = models.CharField(
        max_length=5,
        choices=LanguageCode.CHOICES,
        default=LanguageCode.DEFAULT,
        verbose_name="Language",
    )
    timezone = models.CharField(
        max_length=50,
        default=TimezoneDefault.LUANDA,
        verbose_name="Timezone",
    )

    # Audit timestamps (AbstractUser provides last_login)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # email is USERNAME_FIELD, nothing else required for createsuperuser

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self) -> str:
        return f"{self.full_name} <{self.email}>"

    @property
    def full_name(self) -> str:
        """Returns the user's full name, falling back to email prefix."""
        name = f"{self.first_name} {self.last_name}".strip()
        return name or self.email.split("@")[0]

    @property
    def is_active_account(self) -> bool:
        """Returns True if the account is in active status."""
        return self.status == AccountStatus.ACTIVE

    @property
    def is_suspended(self) -> bool:
        """Returns True if the account has been suspended."""
        return self.status == AccountStatus.SUSPENDED

    def activate(self) -> None:
        """Activate the account and mark email as verified."""
        self.status = AccountStatus.ACTIVE
        self.is_email_verified = True
        self.save(update_fields=["status", "is_email_verified", "updated_at"])

    def suspend(self) -> None:
        """Suspend the account."""
        self.status = AccountStatus.SUSPENDED
        self.save(update_fields=["status", "updated_at"])
