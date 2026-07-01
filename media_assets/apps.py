"""
BOLAYETU — media_assets app configuration

Digital Asset Management (DAM) module.
Centralizes all file management for the platform.
"""

from django.apps import AppConfig


class MediaAssetsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "media_assets"
    verbose_name = "Digital Asset Management"

    def ready(self):
        pass  # noqa: signals registration placeholder
