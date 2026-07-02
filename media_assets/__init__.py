# media_assets — Digital Asset Management (DAM)
# Import subscribers to ensure they are registered at app import time
try:
    from . import subscribers  # noqa: F401
except Exception:
    # Registration is best-effort during startup; log at debug level to avoid noisy failures
    import logging

    logging.getLogger(__name__).debug("media_assets.subscribers import failed during startup")
