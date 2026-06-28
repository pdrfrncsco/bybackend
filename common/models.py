"""
BOLAYETU — Common Base Models

Provides abstract base classes for all domain models.
Every entity in the platform should inherit from these.
"""

import uuid
from django.db import models
from django.utils import timezone


class UUIDModel(models.Model):
    """Abstract model that provides a UUID primary key."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID",
    )

    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    """Abstract model that provides created_at and updated_at timestamps."""

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    """
    Abstract model that provides soft deletion support.
    Records are never permanently deleted — only marked as deleted.
    """

    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Deleted At",
    )

    class Meta:
        abstract = True

    @property
    def is_deleted(self) -> bool:
        """Returns True if the record has been soft deleted."""
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        """Mark this record as deleted without removing it from the database."""
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])

    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.deleted_at = None
        self.save(update_fields=["deleted_at"])


class BaseModel(UUIDModel, TimeStampedModel):
    """
    Base model for all Bolayetu entities.

    Provides:
    - UUID primary key
    - created_at / updated_at audit timestamps

    All domain models should inherit from this class.
    """

    class Meta:
        abstract = True


class AuditModel(UUIDModel, TimeStampedModel, SoftDeleteModel):
    """
    Full audit model with UUID, timestamps and soft delete.

    Use for entities that require complete audit trail and
    must never be permanently deleted (e.g. financial records,
    competition results, player career history).
    """

    class Meta:
        abstract = True
