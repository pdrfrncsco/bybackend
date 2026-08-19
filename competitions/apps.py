from django.apps import AppConfig


class CompetitionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "competitions"
    verbose_name = "Competitions"

    def ready(self):
        try:
            from . import subscribers  # noqa: F401
        except Exception:
            import logging
            logging.getLogger(__name__).exception("Failed to import competitions subscribers")
