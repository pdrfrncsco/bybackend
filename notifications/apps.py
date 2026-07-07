from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "notifications"
    verbose_name = "Notifications"

    def ready(self):
        # Import subscribers to register event handlers when app is ready
        try:
            from . import subscribers  # noqa: F401
        except Exception:
            import logging

            logging.getLogger(__name__).exception("Failed to import notifications.subscribers in ready()")
