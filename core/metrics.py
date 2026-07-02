"""Simple metrics facade.

Provides Counter-like objects backed by prometheus_client when available,
falling back to lightweight in-memory counters (not for production) otherwise.
"""
import logging
from typing import Callable

logger = logging.getLogger(__name__)


class _NoopCounter:
    def __init__(self, name: str, documentation: str = ""):
        self.name = name
        self.documentation = documentation
        self._value = 0

    def inc(self, amount: int = 1) -> None:
        self._value += amount
        logger.debug("Metric %s incremented by %s (now=%s)", self.name, amount, self._value)


def _build_counter(name: str, documentation: str = "") -> _NoopCounter:
    try:
        from prometheus_client import Counter

        return Counter(name, documentation)
    except Exception:
        return _NoopCounter(name, documentation)


# Core event metrics
events_published_total = _build_counter("bolayetu_events_published_total", "Number of domain events published")
events_dispatched_total = _build_counter("bolayetu_events_dispatched_total", "Number of domain events dispatched to handlers")
events_handlers_failed_total = _build_counter("bolayetu_event_handlers_failed_total", "Number of event handler failures")

# Notification delivery metrics
notifications_sent_total = _build_counter("bolayetu_notifications_sent_total", "Number of notifications successfully sent")
notifications_failed_total = _build_counter("bolayetu_notifications_failed_total", "Number of notification delivery failures")
