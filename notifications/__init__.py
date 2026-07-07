# notifications app
# Ensure subscribers are registered on import
try:
    from . import subscribers  # noqa: F401
except Exception:
    import logging
    logging.getLogger(__name__).debug("notifications.subscribers import failed during startup")
