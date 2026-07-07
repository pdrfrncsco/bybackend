"""Lightweight event dispatcher.

- Register subscribers with @subscribe(event_type)
- Publish events with publish_event(event) which will be executed after DB transaction commit
- In-memory deduplication to avoid duplicate handling in the same process (not a replacement for persistent dedupe)
"""
from typing import Callable, Dict, List, Any
import logging
from collections import deque

from django.db import transaction

from .base import Event
from core.metrics import (
    events_published_total,
    events_dispatched_total,
    events_handlers_failed_total,
)

logger = logging.getLogger(__name__)

# registry: event_type -> list of handlers
_subscribers: Dict[str, List[Callable[[Event], None]]] = {}

# in-memory dedupe
_SEEN_MAX = 1000
_seen_ids = set()
_seen_queue = deque()


def _mark_seen(event_id: str) -> None:
    if event_id in _seen_ids:
        return
    _seen_ids.add(event_id)
    _seen_queue.append(event_id)
    if len(_seen_queue) > _SEEN_MAX:
        old = _seen_queue.popleft()
        _seen_ids.discard(old)


def subscribe(event_type: str) -> Callable[[Callable[[Event], None]], Callable[[Event], None]]:
    """Decorator to subscribe a handler to an event type.

    Usage:
        @subscribe("UserRegistered")
        def on_user_registered(event: Event):
            ...
    """

    def decorator(func: Callable[[Event], None]) -> Callable[[Event], None]:
        _subscribers.setdefault(event_type, []).append(func)
        logger.debug("Registered subscriber %s for event %s", func.__name__, event_type)
        return func

    return decorator


def register_handler(event_type: str, func: Callable[[Event], None]) -> None:
    _subscribers.setdefault(event_type, []).append(func)


def get_subscribers(event_type: str) -> List[Callable[[Event], None]]:
    return _subscribers.get(event_type, [])


def _dispatch_sync(event: Event) -> None:
    """Dispatch event to subscribers synchronously in-process."""
    if event.id in _seen_ids:
        logger.debug("Skipping already seen event %s", event.id)
        return

    _mark_seen(event.id)

    handlers = get_subscribers(event.type)
    if not handlers:
        logger.debug("No subscribers for event %s", event.type)
        return

    logger.info("Dispatching event %s to %d subscribers", event.type, len(handlers))
    events_dispatched_total.inc()
    for handler in handlers:
        try:
            handler(event)
        except Exception as exc:
            events_handlers_failed_total.inc()
            logger.exception("Error in event handler %s for event %s: %s", handler, event.type, exc)


def publish_event(event: Event, async_dispatch: bool = False) -> None:
    """Publish an Event after DB transaction commit.

    If async_dispatch=True and a Celery integration exists this can be extended to enqueue a task.
    For now, dispatch is synchronous by default but executed after transaction.commit via on_commit.
    """

    def _on_commit():
        try:
            # mark published metric
            try:
                events_published_total.inc()
            except Exception:
                logger.debug("Failed to inc events_published_total")
            # For now dispatch synchronously in-process. Hook for async enqueue here.
            _dispatch_sync(event)
        except Exception:
            logger.exception("Failed to dispatch event %s", event.type)

    # Ensure events are published only after transaction commit
    try:
        transaction.on_commit(_on_commit)
    except Exception:
        # If no transaction (e.g., non-DB context) or on_commit fails, dispatch immediately
        logger.debug("transaction.on_commit failed or not available, dispatching immediately")
        _on_commit()
