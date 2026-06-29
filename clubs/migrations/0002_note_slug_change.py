"""
Migration note: slug uniqueness

This migration is intentionally empty because the current model already
uses a UniqueConstraint on (tenant, slug) and the Club.slug field does not
have unique=True at the DB field level. No schema change is required.

If you intended to remove a previous unique=True field constraint, run
`manage.py makemigrations` in the project environment and apply the
generated migration after confirming data cleanup for any cross-tenant
slug collisions.
"""

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("clubs", "0001_initial"),
    ]

    operations = [
        # No-op migration: model and DB are already aligned for tenant-scoped slug uniqueness.
    ]
